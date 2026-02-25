using Microsoft.AspNetCore.Mvc;

namespace Milk.AiGateway.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MattermostController : ControllerBase
{
    private readonly IOpenClawService _openClaw;
    private readonly IPiiSecurityService _security;
    private readonly HttpClient _httpClient;

    public MattermostController(IOpenClawService openClaw, IPiiSecurityService security, HttpClient httpClient)
    {
        _openClaw = openClaw;
        _security = security;
        _httpClient = httpClient;
    }

    [HttpPost("webhook")]
    [Consumes("application/x-www-form-urlencoded")]
    public async Task<IActionResult> HandleSlashCommand([FromForm] MattermostSlashCommand req)
    {
        // 1. Immediate response to Mattermost (Avoid 3s timeout)
        var responseUrl = req.Response_Url;
        
        // 2. Start Background Processing
        _ = Task.Run(async () =>
        {
            try {
                // Step A: PII Masking
                var maskedInput = await _security.MaskAsync(req.Text);

                // Step B: AI Inference
                var aiResponse = await _openClaw.ChatAsync(maskedInput, req.Channel_Id);

                // Step C: PII Unmasking
                var finalOutput = await _security.UnmaskAsync(aiResponse);

                // Step D: Async Reply to Mattermost
                await _httpClient.PostAsJsonAsync(responseUrl, new {
                    text = finalOutput,
                    response_type = "in_channel"
                });
            }
            catch (Exception ex) {
                await _httpClient.PostAsJsonAsync(responseUrl, new {
                    text = $"⚠️ AI 服務暫時無法回應：{ex.Message}",
                    response_type = "ephemeral"
                });
            }
        });

        return Ok(new { text = "🥛 Milk AI 正在思考中，請稍候...", response_type = "ephemeral" });
    }
}

public class MattermostSlashCommand
{
    public string Channel_Id { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string Response_Url { get; set; } = string.Empty;
    public string User_Name { get; set; } = string.Empty;
}
