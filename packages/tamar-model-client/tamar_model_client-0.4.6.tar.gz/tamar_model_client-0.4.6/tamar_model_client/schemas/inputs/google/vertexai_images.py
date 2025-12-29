from pydantic import BaseModel
from typing import Optional, Literal


class GoogleVertexAIImagesInput(BaseModel):
    model: str
    prompt: str
    negative_prompt: Optional[str] = None
    number_of_images: int = 1
    aspect_ratio: Optional[Literal["1:1", "9:16", "16:9", "4:3", "3:4"]] = None
    guidance_scale: Optional[float] = None
    language: Optional[str] = None
    seed: Optional[int] = None
    output_gcs_uri: Optional[str] = None
    add_watermark: Optional[bool] = True
    safety_filter_level: Optional[
        Literal["block_most", "block_some", "block_few", "block_fewest"]
    ] = None
    person_generation: Optional[
        Literal["dont_allow", "allow_adult", "allow_all"]
    ] = None

    model_config = {
        "arbitrary_types_allowed": True
    }
