from pathlib import Path
from types import MethodType
from typing import Union
from functools import partial

import sevenn._keys as KEY
import torch
import torch.nn as nn
from sevenn.util import model_from_checkpoint

from franken.data.base import Configuration


def extract_scalar_irrep(data, irreps):
    node_features = data[KEY.NODE_FEATURE]
    scalar_slice = irreps.slices()[0]
    scalar_features = node_features[..., scalar_slice]
    return scalar_features


def franken_sevenn_descriptors(
    self,
    data: Configuration,
    interaction_layer: int,
    extract_after_act: bool = True,
    append_layers: bool = True,
):
    # Convert data to sevenn
    assert data.cell is not None
    sevenn_data = {
        KEY.NODE_FEATURE: data.atomic_numbers,
        KEY.ATOMIC_NUMBERS: data.atomic_numbers,
        KEY.POS: data.atom_pos,
        KEY.EDGE_IDX: data.edge_index,
        KEY.CELL: data.cell,
        KEY.CELL_SHIFT: data.shifts,  # TODO: Check this correct?
        KEY.CELL_VOLUME: torch.einsum(
            "i,i", data.cell[0, :], torch.linalg.cross(data.cell[1, :], data.cell[2, :])
        ),
        KEY.NUM_ATOMS: len(data.atomic_numbers),
        KEY.BATCH: data.batch_ids,
    }

    # From v0.9.3 to v10 sevenn introduced some changes in how models are build
    # (`build_E3_equivariant_model`), removing the EdgePreprocess class before the
    # network itself. The main purpose of EdgePreprocess was to initialize the
    # KEY.EDGE_VEC (r_ij: the vector between atom positions) and KEY.EDGE_LENGTH.
    # We replace that functionality here.
    # NOTE: the original preprocess had some special handling of the PBC cell
    #       when self.is_stress was set to True. We're ignoring all that.
    # NOTE: as comparison to the original EdgePreprocess we assume `is_batch_data`
    #       to be False.
    idx_src = sevenn_data[KEY.EDGE_IDX][0]
    idx_dst = sevenn_data[KEY.EDGE_IDX][1]
    pos = sevenn_data[KEY.POS]
    edge_vec = pos[idx_dst] - pos[idx_src]
    edge_vec = edge_vec + torch.einsum(
        "ni,ij->nj", sevenn_data[KEY.CELL_SHIFT], sevenn_data[KEY.CELL].view(3, 3)
    )
    sevenn_data[KEY.EDGE_VEC] = edge_vec
    sevenn_data[KEY.EDGE_LENGTH] = torch.linalg.norm(edge_vec, dim=-1)

    # Iterate through the model's layers
    # the sanest way to figure out which layer we're at is through the
    # `_modules` attribute of `nn.Sequential` (which the Sevenn network
    # inherits from), which exposes key-value pairs.
    layer_idx = 0
    scalar_features_list = []
    for i, (name, module) in enumerate(self._modules.items()):
        if "self_connection_intro" in name:
            layer_idx += 1

        new_sevenn_data = module(sevenn_data)
        if "equivariant_gate" in name:
            if extract_after_act:
                scalar_features = extract_scalar_irrep(
                    new_sevenn_data, module.gate.irreps_out
                )
            else:
                scalar_features = extract_scalar_irrep(
                    sevenn_data, module.gate.irreps_in
                )
            if append_layers:
                scalar_features_list.append(scalar_features)
            else:
                scalar_features_list[0] = scalar_features
            if layer_idx == interaction_layer:
                break
        sevenn_data = new_sevenn_data

    return torch.cat(scalar_features_list, dim=-1)


def franken_sevenn_num_params(self) -> int:
    return sum(p.numel() for p in self.parameters())


def franken_sevenn_feature_dim(
    self,
    interaction_layer: int,
    extract_after_act: bool = True,
    append_layers: bool = True,
):
    layer_idx = 0
    tot_feat_dim = 0
    for i, (name, module) in enumerate(self._modules.items()):
        if "self_connection_intro" in name:
            layer_idx += 1
        if "equivariant_gate" in name:
            if extract_after_act:
                new_feat_dim = module.gate.irreps_out.count("0e")
            else:
                new_feat_dim = module.gate.irreps_in.count("0e")
            if append_layers:
                tot_feat_dim += new_feat_dim
            else:
                tot_feat_dim = new_feat_dim
            if layer_idx == interaction_layer:
                break
    return tot_feat_dim


class FrankenSevenn:
    @staticmethod
    def load_from_checkpoint(
        trainer_ckpt: Union[str, Path],
        gnn_backbone_id: str,
        interaction_block: int,
        extract_after_act: bool = True,
        append_layers: bool = True,
    ):
        sevenn, config = model_from_checkpoint(str(trainer_ckpt))
        assert isinstance(sevenn, nn.Module)
        sevenn.descriptors = MethodType(  # type: ignore
            partial(
                franken_sevenn_descriptors,
                interaction_layer=interaction_block,
                extract_after_act=extract_after_act,
                append_layers=append_layers,
            ),
            sevenn,
        )
        sevenn.num_params = MethodType(franken_sevenn_num_params, sevenn)  # type: ignore
        sevenn.feature_dim = MethodType(  # type: ignore
            partial(
                franken_sevenn_feature_dim,
                interaction_layer=interaction_block,
                extract_after_act=extract_after_act,
                append_layers=append_layers,
            ),
            sevenn,
        )

        def init_args(self):
            return {
                "gnn_backbone_id": gnn_backbone_id,
                "interaction_block": interaction_block,
                "extract_after_act": extract_after_act,
                "append_layers": append_layers,
            }

        sevenn.init_args = MethodType(init_args, sevenn)  # type: ignore
        return sevenn
