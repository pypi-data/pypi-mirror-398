import logging
import sys
import os


def rital():
    try:
        from datamaestro import prepare_dataset
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    for dataset_id in [
        "com.github.aagohary.canard",
        "irds.antique.train",
        "irds.antique.test",
    ]:
        logging.info("Preparing %s", dataset_id)
        prepare_dataset(dataset_id)

    try:
        from transformers import AutoTokenizer, AutoModelForMaskedLM
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    for hf_id in ["Luyu/co-condenser-marco", "huawei-noah/TinyBERT_General_4L_312D"]:
        AutoTokenizer.from_pretrained(hf_id)
        AutoModelForMaskedLM.from_pretrained(hf_id)


def llm():
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            AutoModelForSequenceClassification,
        )
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    try:
        import datasets
    except ModuleNotFoundError:
        logging.info("datasets n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    HF_MODELS = [
        # Course 2
        ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", AutoModelForCausalLM),
        ("distilbert-base-uncased", AutoModelForSequenceClassification),
        (
            "distilbert-base-uncased-finetuned-sst-2-english",
            AutoModelForSequenceClassification,
        ),
    ]
    for hf_id, base_class in HF_MODELS:
        AutoTokenizer.from_pretrained(hf_id)
        base_class.from_pretrained(hf_id)

    # IMDB
    datasets.load_dataset("imdb", split="train")


def amal():
    try:
        from datamaestro import prepare_dataset
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    try:
        import datasets
    except ModuleNotFoundError:
        logging.info("datasets n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    # From datamaestro
    for dataset_id in [
        "com.lecun.mnist",
        "edu.uci.boston",
        "org.universaldependencies.french.gsd",
        "edu.stanford.aclimdb",
        "edu.stanford.glove.6b.50",
    ]:
        logging.info("Preparing %s", dataset_id)
        prepare_dataset(dataset_id)

    # Hugging Face (CelebA)
    datasets.load_dataset(
        "nielsr/CelebA-faces", os.environ.get("HF_DATASETS_CACHEDIR", None)
    )
