# `pipecat-assistant`

## Deploying

The follow instructions are for deploying for local use or to access through [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/).

Adapt the service files for your setup, such as the `WorkingDirectory` for the server and client.
Make sure that the `BOT_START_URL` in `client/.env.local` corresponds to the port specified for executing the bot in the server service.

Then, copy the service files:

```
sudo cp server.service.example /etc/systemd/system/pipecat-assistant-server.service
sudo cp client.service.example /etc/systemd/system/pipecat-assistant-client.service
```

Activate service:

```
sudo systemctl daemon-reload
sudo systemctl enable pipecat-assistant-server.service
sudo systemctl enable pipecat-assistant-client.service
sudo systemctl start pipecat-assistant-server.service
sudo systemctl start pipecat-assistant-client.service
```

Check status and logs:

```
systemctl status pipecat-assistant-server.service
systemctl status pipecat-assistant-client.service

journalctl -u pipecat-assistant-server.service -f
journalctl -u pipecat-assistant-client.service -f
```

Stop:

```
sudo systemctl stop pipecat-assistant-server.service
sudo systemctl stop pipecat-assistant-client.service
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
