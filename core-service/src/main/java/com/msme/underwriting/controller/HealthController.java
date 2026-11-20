package com.msme.underwriting.controller;

import com.msme.underwriting.client.AiServiceClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
public class HealthController {

    private final AiServiceClient aiServiceClient;

    public HealthController(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getHealth() {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "UP");
        response.put("service", "core-service");
        response.put("timestamp", Instant.now().toString());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/api/ai-service/health")
    public ResponseEntity<Map<String, Object>> getAiHealth() {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("core_status", "UP");
        payload.put("ai_service", aiServiceClient.fetchAiHealth());
        payload.put("timestamp", Instant.now().toString());
        return ResponseEntity.ok(payload);
    }
}
