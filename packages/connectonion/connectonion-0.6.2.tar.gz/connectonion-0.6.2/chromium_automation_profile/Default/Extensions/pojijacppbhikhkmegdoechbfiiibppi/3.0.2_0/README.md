# Remote for Slides Chrome Extension

## Setup
```
# 1. Install
> npm install

# 2. Run in dev mode
> npm run dev

# 3. Build
> npm run build

# 4. Build and generate .zip file
> npm run generate
```

## Setup Chrome Web Store API

1. Go to [GitLab CI/CI Settings](https://gitlab.com/remote-for-slides/remote-for-slides-extension/-/settings/ci_cd)

2. Get the variables value from the CI/CI Settings and set temporary environment variables in your terminal:
```
WEBSTORE_APP_ID=xxx
WEBSTORE_CLIENT_ID=xxx
WEBSTORE_CLIENT_SECRET=xxx
```

3. Executing the following command to get the URL to retrieve the access token:
```
echo "https://accounts.google.com/o/oauth2/auth?response_type=code&scope=https://www.googleapis.com/auth/chromewebstore&client_id=$WEBSTORE_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob"
```

4. Set the authorization code as temporary environment variables in your terminal
```
WEBSTORE_AUTHORIZATION_CODE=xxx
```

5. Executing the following command to get the URL to retrieve the refresh token:
```
curl "https://accounts.google.com/o/oauth2/token" -d "client_id=$WEBSTORE_CLIENT_ID&client_secret=$WEBSTORE_CLIENT_SECRET&code=$WEBSTORE_AUTHORIZATION_CODE&grant_type=authorization_code&redirect_uri=urn:ietf:wg:oauth:2.0:oob"
```

6. Copy the `refresh_token` and update the value for `WEBSTORE_REFRESH_TOKEN` in CI/CI Settings.

## Publishing Chrome Extension
Once the code is pushed to master branch, the CI will automatically build and upload the package to the [Chrome Web Store Dashboard](
https://chrome.google.com/webstore/devconsole/d0760395-4adc-4212-b64c-e8c7e781c952/pojijacppbhikhkmegdoechbfiiibppi/edit/package).
