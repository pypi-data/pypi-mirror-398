function fn() {
    karate.configure('ssl', { trustAll: true });

    let config = {};

    config.baseUrl = karate.properties['baseUrl'];

    config.cognitoUrl = karate.properties['cognitoUrl'];

    config.clientId = karate.properties['clientId'];

    config.clientSecret = karate.properties['clientSecret'];

    return config
}