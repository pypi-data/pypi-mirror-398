from setuptools import setup, find_packages

def read_reqs(path):
    with open(path, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

common_requirements = read_reqs("requirements.txt")
doc_loader = read_reqs("packages/doc_loader.txt")
index = read_reqs("packages/index.txt")
rag = read_reqs("packages/rag.txt")
tools = read_reqs("packages/tools.txt")
evals = read_reqs("packages/evals.txt")
chat = read_reqs("packages/chat.txt")
agents = read_reqs("packages/agents.txt")

all_extras = list(common_requirements + doc_loader + index + rag+ tools + evals + chat + agents)

setup(
    name="fabriq",
    version="0.2.9.5",
    description="Fabriq is a Python SDK for developing quick, low code Generative AI solutions.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    author="Aaryan Verma",
    url="https://github.com/Aaryanverma/fabriq",
    packages=find_packages(),
    install_requires=common_requirements,
    entry_points={
        "console_scripts": [
            "fabriq-chat-cli=fabriq.chatbot.chat_cli:main",
            "fabriq-chat-ui=fabriq.chatbot.ui_runner:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
    extras_require={
        'chat': chat,
        'agents': agents,
        'doc_loader': doc_loader,
        'index': index,
        'rag': rag,
        'tools': tools,
        'evals': evals,
        'all': all_extras
    }
)