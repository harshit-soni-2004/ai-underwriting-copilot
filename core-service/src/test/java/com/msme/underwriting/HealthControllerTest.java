package com.msme.underwriting;

import com.msme.underwriting.client.AiServiceClient;
import com.msme.underwriting.controller.HealthController;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(HealthController.class)
@ActiveProfiles("test")
class HealthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AiServiceClient aiServiceClient;

    @Test
    @DisplayName("GET /health returns 200 with UP status")
    void testCoreHealthEndpoint() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.service").value("core-service"));
    }

    @Test
    @DisplayName("GET /api/ai-service/health relays AI service status")
    void testAiHealthEndpoint() throws Exception {
        given(aiServiceClient.fetchAiHealth()).willReturn(Map.of("status", "OK", "service", "ai-service"));

        mockMvc.perform(get("/api/ai-service/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.core_status").value("UP"))
                .andExpect(jsonPath("$.ai_service.status").value("OK"));
    }
}
