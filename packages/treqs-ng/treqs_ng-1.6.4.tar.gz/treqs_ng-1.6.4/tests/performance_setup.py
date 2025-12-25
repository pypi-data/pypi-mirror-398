import os
import random


def generate_performance_test_data(
    test_dir: str,
    SHReq_count: int = 625,
    SysReq_count: int = 1875,
    Test_count: int = 2500,
) -> None:
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # Generate SHReq_count SHReq
    with open(test_dir + os.sep + "shreqs.md", "w") as f:
        f.write(
            "# Generated Stakeholder Requirements for Performance evaluation\n\n"
        )
        for i in range(1, SHReq_count + 1):
            f.write(
                f'<treqs-element id="SHReq{i}" type="SHReq">'
                f"## SHReq {i}"
                f"</treqs-element>\n"
            )

    # Generate SysReq_count SySReq with random links to a SHReq
    with open(test_dir + os.sep + "sysreqs.md", "w") as f:
        f.write(
            "# Generated System Requirements for Performance evaluation\n\n"
        )
        for i in range(1, SysReq_count + 1):
            f.write(
                f'<treqs-element id="SysReq{i}" type="SysReq">'
                f"## SysReq {i}"
                f'<treqs-link target="SHReq{random.randint(1, SHReq_count)}" type="childOf" />'
                f"</treqs-element>\n"
            )

    # Generate Test_count Test elements
    with open(test_dir + os.sep + "tests.md", "w") as f:
        f.write("# Generated Tests for Performance evaluation\n\n")
        for i in range(1, Test_count + 1):
            f.write(
                f'<treqs-element id="Test{i}" type="Test">'
                f"## Test {i}"
                f'<treqs-link target="SysReq{random.randint(1, SHReq_count)}" type="tests" />'
                f"</treqs-element>\n"
            )
        for i in range(SysReq_count + 1, Test_count + 1):
            f.write(
                f'<treqs-element id="Test{i}" type="Test">'
                f"## Test {i}"
                f'<treqs-link target="SysReq{random.randint(1, SysReq_count)}" type="tests" />'
                f"</treqs-element>\n"
            )
