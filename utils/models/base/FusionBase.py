from utils.models.base.IntermediateModelBase import IntermediateModelBase


class FusionBase(IntermediateModelBase):
    def __init__(self, config, layer=3, in_channels=13, kd_flag=True):
        super(FusionBase, self).__init__(config, layer, in_channels, kd_flag)
        self.num_agent = 0

    def fusion(self):
        raise NotImplementedError("Please implement this method for specific fusion strategies")

    def forward(self, bevs, trans_matrices, num_agent_tensor, batch_size=1):

        bevs = bevs.permute(0, 1, 4, 2, 3)  # (Batch, seq, z, h, w)
        encoded_layers = self.u_encoder(bevs)
        device = bevs.device

        feat_maps, size = super().get_feature_maps_and_size(encoded_layers)

        # print(feat_maps[0,0])

        feat_list = super().build_feature_list(batch_size, feat_maps)

        local_com_mat = super().build_local_communication_matrix(
            feat_list)  # [2 5 512 16 16] [batch, agent, channel, height, width]
        local_com_mat_update = super().build_local_communication_matrix(feat_list)  # to avoid the inplace operation

        for b in range(batch_size):
            self.num_agent = num_agent_tensor[b, 0]
            for i in range(self.num_agent):
                self.tg_agent = local_com_mat[b, i]
                self.neighbor_feat_list = []
                self.neighbor_feat_list.append(self.tg_agent)
                all_warp = trans_matrices[b, i]  # transformation [2 5 5 4 4]

                super().build_neighbors_feature_list(b, i, all_warp, self.num_agent, local_com_mat,
                                                     device, size)

                # feature update
                local_com_mat_update[b, i] = self.fusion()

        # weighted feature maps is passed to decoder
        feat_fuse_mat = super().agents_to_batch(local_com_mat_update)
        # print(feat_fuse_mat[0,0])

        # x = super().get_decoded_layers([encoded_layers[0], encoded_layers[1], encoded_layers[2], encoded_layers[3]], feat_fuse_mat[:,0], feat_fuse_mat[:,1], batch_size)
        
        x = self.decoder(encoded_layers[0], encoded_layers[1], encoded_layers[2], feat_fuse_mat, batch_size)

        return x

        # if self.kd_flag == 1:
        #     return (result, *decoded_layers, feat_fuse_mat)
        # else:
        #     return result
