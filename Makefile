QEDESK := ./bin/qedesk

.PHONY: start stop restart status shell files contracts sync blueprint serve prepare cache build-lean pdf agent audit cost clean docker-clean

start:
	$(QEDESK) start

stop:
	$(QEDESK) stop

restart:
	$(QEDESK) restart

status:
	$(QEDESK) status

shell:
	$(QEDESK) shell

files:
	$(QEDESK) files

contracts:
	$(QEDESK) contracts

sync:
	$(QEDESK) sync

blueprint:
	$(QEDESK) blueprint

serve:
	$(QEDESK) serve

prepare:
	$(QEDESK) prepare

cache:
	$(QEDESK) cache

build-lean:
	$(QEDESK) lean

pdf:
	$(QEDESK) pdf

agent:
	$(QEDESK) agent

audit:
	$(QEDESK) audit

cost:
	$(QEDESK) cost

clean:
	$(QEDESK) clean

docker-clean:
	$(QEDESK) docker-clean
