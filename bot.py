import pkgutil
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import config
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler.saya import GraiaSchedulerBehaviour

from Config import config_data, save_config

app = Ariadne(
    config(
        # host=config_data["MAH"]["host"],
        verify_key=config_data["MAH"]["verify_key"],
        account=config_data["MAH"]["account"],
    ),
)

saya = app.create(Saya)
saya.install_behaviours(
    app.create(BroadcastBehaviour),
    app.create(GraiaSchedulerBehaviour)
)

with saya.module_context():
    for module_info in pkgutil.iter_modules(["modules"]):
        saya.require("modules." + module_info.name)

with saya.module_context():
    for control_info in pkgutil.iter_modules(["control"]):
        saya.require("control." + control_info.name)

app.launch_blocking()
save_config()
