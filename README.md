# Geobot, a Geography Python Twitter Bot - The GeoServer Component

Made for the [dev.to Digital Ocean's Hackathon](https://dev.to/devteam/announcing-the-digitalocean-app-platform-hackathon-on-dev-2i1k). 

This is the geo-server component. [Here](https://github.com/davidedelpapa/geobotshow) You can find the tweetbot used to connect to this server.

You can try it with the following:

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/davidedelpapa/geobot/tree/master)

## Series

If you want to know more, please follow the dev.to series:

- [First installment](https://dev.to/davidedelpapa/dev-digitalocean-hackathon-geobot-a-geography-python-twitter-bot-tut-01-470o): setting the geobot server as DO App Platform Service
- [Second installment](https://dev.to/davidedelpapa/dev-digitalocean-hackathon-geobot-a-geography-python-twitter-bot-tut-02-20j9): setting a twitter bot as DO App Platform Worker
- [Third installment](https://dev.to/davidedelpapa/dev-digitalocean-hackathon-geobot-a-geography-python-twitter-bot-tut-03-9mk): adding geographic capabilities
- [Hackathon Submission](https://dev.to/davidedelpapa/dev-digitalocean-hackathon-geobot-a-geography-python-twitter-bot-submission-form-250a): Submission Post (contains some rationale and reasoning about the project)

## LICENSE

The software is licensed under the MIT license. However, consider that it retrieves data from [Mapbox](https://www.mapbox.com/) and [OpenStreetMap](https://www.openstreetmap.org/). Refer also to their licenses.

The system can be adapted to be tile-server agnostic (i.e., use a provider other than Mapbox).
