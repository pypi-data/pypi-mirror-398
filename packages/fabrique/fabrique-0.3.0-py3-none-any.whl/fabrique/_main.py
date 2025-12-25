from fabrique.sampling import *
from fabrique.tokenizer_utils import encode_batch

TMPL = """<start_of_turn>user\n{}<end_of_turn>\n<start_of_turn>model\n"""


def main0():
    sampler = Sampler.load_model("gemma-3-4b-it")
    tokenizer, model = sampler.tokenizer, sampler.model
    prompts = [
        """<start_of_turn>user\n<start_of_image>Describe the image in a few sentences<end_of_turn>\n<start_of_turn>model\n"""
    ]
    prompt_tokens = encode_batch(tokenizer, prompts)
    images = jnp.array(Image.open("tests/bird.jpg"))[None, None, ...]

    max_length: int = 4096
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 50
    pad_to_multiple_of: int = 128
    cache_dtype: jnp.dtype = jnp.bfloat16
    rngs: nnx.Rngs = nnx.Rngs(0)
    rng = rngs()
    eos_token_id: int | tuple[int] = 1


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
        rng=rngs(),
    )
    completion = tokenizer.decode(out_tokens[0])



def main():
    sampler = Sampler.load_model("gemma-3-4b-it")
    tokenizer, model = sampler.tokenizer, sampler.model
    prompts = [
        TMPL.format("How much is 2 + 2?"),
        TMPL.format(
            "You are the best mathematician in history. Your solve " +
            "the most complicated tasks. Now you need to answer the " +
            "following question in the most concise way: how much is 2 + 2?"
        )
    ]
    tokens_batch = encode_batch(tokenizer, prompts)
    tokens_pad = encode_batch(tokenizer, prompts[0:1], pad_to_multiple_of=128)

    # batch sampling
    out_batch = sample(model, tokens_batch)
    tokenizer.decode(out_batch[0, :])

    # single seq batch sampling
    out_batch_0 = sample(model, tokens_batch[0:1, :])
    tokenizer.decode(out_batch_0[0, :])


    out_pad = sample(model, tokens_pad)
    tokenizer.decode(out_pad[0, :])


def main2():
    self = Sampler.load_model("gemma-3-4b-it")
    tokenizer, model = self.tokenizer, self.model
    prompt = TMPL.format("How much is 2 + 2?")

    images: jax.Array | Image.Image | list[Image.Image] | None = None
    max_length: int = 4096
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 50
    pad_to_multiple_of: int = 128
    cache_dtype: jnp.dtype = jnp.bfloat16
    rngs: nnx.Rngs = nnx.Rngs(0)
    rng = rngs()
    eos_token_id: int | tuple[int] = 1


    prompt_tokens = encode_batch(
        self.tokenizer, [prompt], pad_to_multiple_of=pad_to_multiple_of
    )
    st = self.tokenizer.special_tokens

    out_tokens = sample(model, prompt_tokens)
    tokenizer.decode(out_tokens[0])

    # TODO: used_cache_length points to the last non-padding token,
    #   but should point to the last input token instead


    # TODO: sampling is now broken in tests