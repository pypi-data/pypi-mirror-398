from PIL import Image
import jax
import jax.numpy as jnp
from flax import nnx
from fabrique.sampling import Sampler, sample
from fabrique.tokenizer_utils import encode_batch
from fabrique.models.gemma.vision_utils import ViTModel


def main():
    rngs = nnx.Rngs(0)
    sampler = Sampler.load_model("gemma-3-4b-it")
    ve = sampler.model.vision_encoder

    tokenizer, model = sampler.tokenizer, sampler.model

    prompts = [
        """<start_of_turn>user\n<start_of_image>Describe the image in a few sentences<end_of_turn>\n<start_of_turn>model\n"""
    ]
    prompt_tokens = encode_batch(tokenizer, prompts)
    # images = jnp.array(Image.open("tests/bird.jpg"))[None, None, ...]
    # patches = ve.patchify_images(images)
    # nnx.jit(lambda ve, p: ve(patches=p))(ve, patches)  # fails


    vit = ve.siglip_encoder
    pure_vit = ViTModel(rngs=rngs)
    image = jax.random.normal(rngs(), (1, 896, 896, 3))
    vit(image)   # works
    nnx.jit(lambda vit, image: vit(image))(pure_vit, image)  # works
    nnx.jit(lambda vit, image: vit(image))(vit, image)  # fails: Argument 'vit.states[0][10]' of shape uint32[] of type <class 'jax.ShapeDtypeStruct'> is not a valid JAX type.



    out_tokens = sample(
        model,
        prompt_tokens,
        images=images,
        eos_token_id=(
            tokenizer.special_tokens.EOS,
            tokenizer.special_tokens.END_OF_TURN,
        ),
        max_length=512,
        temperature=1,
        rng=jax.random.key(0),
    )