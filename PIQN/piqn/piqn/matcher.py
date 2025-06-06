import torch
from scipy.optimize import linear_sum_assignment
# from lapsolver import solve_dense
from .lap import auction_lap
from torch import nn
from torch.nn import functional as F

class HungarianMatcher(nn.Module):
    """This class computes an assignment between the targets and the predictions of the network
    For efficiency reasons, the targets don't include the no_object. Because of this, in general,
    there are more predictions than targets. In this case, we do a 1-to-1 matching of the best predictions,
    while the others are un-matched (and thus treated as non-objects).
    """

    def __init__(self, cost_class: float = 1, cost_span: float = 1, solver = "hungarian"):
        """Creates the matcher
        Params:
            cost_class: This is the relative weight of the classification error in the matching cost
            cost_bbox: This is the relative weight of the L1 error of the bounding box coordinates in the matching cost
            cost_giou: This is the relative weight of the giou loss of the bounding box in the matching cost
        """
        super().__init__()
        self.cost_class = cost_class
        self.cost_span = cost_span
        self.solver = solver

    @torch.no_grad()
    def forward(self, outputs, targets):
        """ Performs the matching
        Params:
            outputs: This is a dict that contains at least these entries:
                 "pred_logits": Tensor of dim [batch_size, num_queries, num_classes] with the classification logits
                 "pred_boxes": Tensor of dim [batch_size, num_queries, 4] with the predicted box coordinates
            targets: This is a list of targets (len(targets) = batch_size), where each target is a dict containing:
                 "labels": Tensor of dim [num_target_boxes] (where num_target_boxes is the number of ground-truth
                           objects in the target) containing the class labels
                 "boxes": Tensor of dim [num_target_boxes, 4] containing the target box coordinates
        Returns:
            A list of size batch_size, containing tuples of (index_i, index_j) where:
                - index_i is the indices of the selected predictions (in order)
                - index_j is the indices of the corresponding selected targets (in order)
            For each batch element, it holds:
                len(index_i) = len(index_j) = min(num_queries, num_target_boxes)
        """

        if self.solver == "order":
            sizes = targets["sizes"]
            indices = [(list(range(size)),list(range(size))) for size in sizes]
        else:
            bs, num_queries = outputs["pred_logits"].shape[:2]

            a = torch.isnan(outputs["pred_logits"]).any()
            if a:
                print("harl")

            # We flatten to compute the cost matrices in a batch
            out_prob = F.log_softmax(outputs["pred_logits"].flatten(0,1),-1) #outputs["pred_logits"].flatten(0, 1).softmax(dim=-1) # [batch_size * num_queries, 8]
            out_prob = torch.exp(out_prob)

            a = torch.isnan(out_prob).any()
            if a:
                print("harl")

            entity_left = outputs["pred_left"].flatten(0, 1)
            entity_right = outputs["pred_right"].flatten(0, 1) # [batch_size * num_queries]

            a = torch.isnan(entity_left).any()
            if a:
                print("harl")
            a = torch.isnan(entity_right).any()
            if a:
                print("harl")

            gt_ids = targets["labels"]
            gt_left = targets["gt_left"]
            gt_right = targets["gt_right"]

            a = torch.isnan(gt_ids).any()
            if a:
                print("harl")
            a = torch.isnan(gt_left).any()
            if a:
                print("harl")

            a = torch.isnan(gt_right).any()
            if a:
                print("harl")

            # import pdb;pdb.set_trace()
            cost_class = -out_prob[:, gt_ids]

            a = torch.isnan(cost_class).any()
            if a:
                print("harl")

            cost_span = -(entity_left[:, gt_left] + entity_right[:, gt_right])

            a = torch.isnan(cost_span).any()
            if a:
                print("harl")

            # Final cost matrix
            C = self.cost_span * cost_span + self.cost_class * cost_class

            a = torch.isnan(C).any()
            if a:
                print("harl")

            C = C.view(bs, num_queries, -1)

            sizes = targets["sizes"]
            indices = None
            
            if self.solver == "hungarian":
                C = C.cpu()
                indices = [linear_sum_assignment(c[i]) for i, c in enumerate(C.split(sizes, -1))]
            if self.solver == "auction":
                indices = [auction_lap(c[i])[:2] for i, c in enumerate(C.split(sizes, -1))]

        return [(torch.as_tensor(i, dtype=torch.int64), torch.as_tensor(j, dtype=torch.int64)) for i, j in indices]