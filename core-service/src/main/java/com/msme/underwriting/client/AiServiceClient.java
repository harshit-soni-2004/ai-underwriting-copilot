package com.msme.underwriting.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Collections;
import java.util.Map;

@Service
public class AiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);
    private final RestClient restClient;

    public AiServiceClient(RestClient aiRestClient) {
        this.restClient = aiRestClient;
    }

    public Map<String, Object> fetchAiHealth() {
        try {
            return restClient.get()
                    .uri("/health")
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception ex) {
            log.warn("Health probe to AI service failed: {}", ex.getMessage());
            return Collections.singletonMap("status", "UNREACHABLE");
        }
    }
}
