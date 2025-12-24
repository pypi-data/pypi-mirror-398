from IPython import get_ipython

example_sources = dict()

def example(module, label: str = "default"):
    # Tra cứu ví dụ trong từ điển
    code = example_sources.get(module, {}).get(label, {}).get("code")
    if code is None:
        raise ValueError(f"Chưa có ví dụ minh họa cho module")

    # Chèn code vào cell tiếp theo
    get_ipython().set_next_input(str(code).strip(), replace=False)


def assign_example(module, code, label: str = "default"):
    example_sources.update({
        module: {
            label: {
                "code": code
            }
        }
    })
