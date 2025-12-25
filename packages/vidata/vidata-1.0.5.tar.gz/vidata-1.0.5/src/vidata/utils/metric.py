import numpy as np
import torch


class ConfusionMatrixNP:
    def __init__(self, num_classes, ignore_index: int = None, dtype=np.uint64):
        self.num_classes = num_classes
        self.ignore_index = ignore_index
        self.mat = np.zeros((self.num_classes, self.num_classes), dtype=dtype)

    def update(self, pred: np.ndarray, gt: np.ndarray) -> None:
        #  If pred are probs/logits, reduce to class ids  e.g. (B,C,H,W) probs/logits
        if np.issubdtype(pred.dtype, np.floating) and pred.ndim == gt.ndim + 1:
            pred = pred.argmax(axis=1)

        # Flatten
        p = np.ravel(pred)
        g = np.ravel(gt)

        # Everything valid except ignore_index
        valid = (g != self.ignore_index) if self.ignore_index is not None else slice(None)

        # Encode (gt, pred) -> single index k = n*gt + pred
        inds = (self.num_classes * g[valid].astype(np.intp, copy=False)) + p[valid].astype(
            np.intp, copy=False
        )
        # 1D histogram -> reshape to (n, n)
        conf = np.bincount(inds, minlength=self.num_classes * self.num_classes).reshape(
            self.num_classes, self.num_classes
        )

        # Accumulate
        self.mat += conf.astype(self.mat.dtype, copy=False)

    def reset(self) -> None:
        self.mat.fill(0)

    def value(self) -> np.ndarray:
        return self.mat.copy()


class ConfusionMatrixTorch:
    def __init__(
        self,
        num_classes,
        ignore_index: int | None = None,
        dtype: torch.dtype = torch.long,
        device: torch.device | None = None,
    ):
        self.num_classes = int(num_classes)
        self.ignore_index = ignore_index
        self.mat = torch.zeros(
            (self.num_classes, self.num_classes),
            dtype=dtype,
            device=(device or torch.device("cpu")),
        )

    @torch.no_grad()
    def update(self, pred: torch.Tensor, gt: torch.Tensor) -> None:
        # ensure tensors are on the same device as the accumulator
        if pred.device != self.mat.device:
            pred = pred.to(self.mat.device, non_blocking=True)
        if gt.device != self.mat.device:
            gt = gt.to(self.mat.device, non_blocking=True)

        # If pred are probs/logits, reduce to class ids (e.g. (B,C,H,W) -> argmax over dim=1)
        if pred.dtype.is_floating_point and pred.dim() == gt.dim() + 1:
            pred = pred.argmax(dim=1)

        # Flatten
        p = pred.reshape(-1)
        g = gt.reshape(-1)

        # Everything valid except ignore_index
        if self.ignore_index is not None:
            valid = g != self.ignore_index
            if not torch.any(valid):
                return
            p = p[valid]
            g = g[valid]

        # Encode (gt, pred) -> single index k = n*gt + pred
        inds = (self.num_classes * g.to(torch.int64)) + p.to(torch.int64)

        # 1D histogram -> reshape to (n, n)
        conf = torch.bincount(inds, minlength=self.num_classes * self.num_classes).reshape(
            self.num_classes, self.num_classes
        )

        # Accumulate
        self.mat += conf.to(self.mat.dtype)

    def reset(self) -> None:
        self.mat.zero_()

    def value(self) -> torch.Tensor:
        return self.mat.clone()


if __name__ == "__main__":
    from vidata.task_manager import SemanticSegmentationManager

    nclasses = 4
    prediction = SemanticSegmentationManager.random((2, 2), nclasses)
    prediction = np.random.rand(3, nclasses, 2, 2)
    print(prediction.shape, prediction.dtype)
    mask = SemanticSegmentationManager.random((3, 2, 2), nclasses)

    cm = ConfusionMatrix(nclasses)
    cm.update(prediction, mask)
    print(cm.value())
    cm.update(prediction, mask)
    print(cm.value())
    cm.reset()
    print(cm.value())

    # confmat = np.zeros((num_classes,num_classes))
    #
    # print(confmat.shape)
    #
    # confmat_ml=np.zeros((num_classes,2,2))
    # print(confmat_ml.shape)
