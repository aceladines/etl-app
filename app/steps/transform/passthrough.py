from app.steps.transform.base_transform import BaseTransformStep


class PassthroughTransform(BaseTransformStep):
    """No-op transform — returns rows unchanged."""

    def transform_batch(self, batch: list[dict]) -> list[dict]:
        return batch
