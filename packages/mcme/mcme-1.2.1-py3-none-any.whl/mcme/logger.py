import logging

log = logging.getLogger("mcme-cli")
log.setLevel(logging.INFO)
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
log.addHandler(console)
log.propagate = True
