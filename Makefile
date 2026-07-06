QEDESK := ./bin/qedesk

.PHONY: start stop restart status shell build-lean pdf agent clean docker-clean

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

build-lean:
	$(QEDESK) lean

pdf:
	$(QEDESK) pdf

agent:
	$(QEDESK) agent

clean:
	$(QEDESK) clean

docker-clean:
	$(QEDESK) docker-clean
