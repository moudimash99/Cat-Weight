# Cat-Weight

<!-- where-it-runs: made by Infra/scripts/readmes.py from Infra/services.yaml; edit the entry there, not here -->
## Where it runs

**cat-weight** (web-app, production): Cat weight tracker (Flask + SQLite).

| | |
|---|---|
| Runs | k8s apps/Deployment cat-weight on acer-laptop |
| Address | https://cat.machaka.net |
| Deploy | Build on the server from ~/Cat-Weight (tag = commit), docker save, copy to the Acer and `sudo k3s ctr images import` there (README "For an app on the Acer"), set the tag, apply. |
| Manifest | Infra/k8s/apps/cat-weight/cat-weight.yaml |
| Image | cat-weight, built on the server from ~/Cat-Weight, tag = commit (pull Never) |
| Data | hostPath /srv/apps/cat-weight on the Acer (SQLite); also read by the lab (read-only) |
| Check | Pod Ready (tcpSocket :8002); Homepage siteMonitor http://cat-weight.apps.svc |

Where what runs differs from the code:

- The repo is in Documents/GitHub, not Documents/Coding; Coding/Weight_Food_Tracker is an empty folder, not this app.

From the home's service catalog, [Infra/services.yaml](https://github.com/moudimash99/Infra/blob/main/services.yaml) (entries `cat-weight`). What runs right now,
its health, and code here that is not deployed yet: `python scripts/status.py` in the Infra repo.
<!-- /where-it-runs -->
