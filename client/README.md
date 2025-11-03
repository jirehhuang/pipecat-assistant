# Client setup instructions

Navigate to the `client/` directory:

```
cd client
```

Configure environment by updating `BOT_START_URL` to use the desired port. If exposing via [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/) for example, specify and `ALLOWED_DEV_ORIGIN` as well.

```
cp env.example .env.local
```

Install local [`voice-ui-kit`](https://github.com/pipecat-ai/voice-ui-kit):

```
cd ../voice-ui-kit  # ./voice-ui-kit
npm install

cd package  # ./voice-ui-kit/package
npm install
npm run build
```

Install client:

```
cd ../../client
npm install
```

For development:

```
npm run dev
```

For production:

```
npm run build
npm run start
```
