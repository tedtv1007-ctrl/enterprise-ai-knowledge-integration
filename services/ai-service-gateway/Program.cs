using Microsoft.AspNetCore.Mvc;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddHttpClient();

// Configuration for OpenClaw and Security Sidecar
builder.Services.AddScoped<IOpenClawService, OpenClawService>();
builder.Services.AddScoped<IPiiSecurityService, PiiSecurityService>();

var app = builder.Build();

app.UseAuthorization();
app.MapControllers();

app.Run();

public interface IOpenClawService {
    Task<string> ChatAsync(string message, string channelId);
}

public interface IPiiSecurityService {
    Task<string> MaskAsync(string text);
    Task<string> UnmaskAsync(string text);
}

public class OpenClawService : IOpenClawService {
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _config;

    public OpenClawService(HttpClient httpClient, IConfiguration config) {
        _httpClient = httpClient;
        _config = config;
    }

    public async Task<string> ChatAsync(string message, string channelId) {
        // Implementation for calling OpenClaw API
        return $"AI Response for {channelId}: {message}"; 
    }
}

public class PiiSecurityService : IPiiSecurityService {
    private readonly HttpClient _httpClient;

    public PiiSecurityService(HttpClient httpClient) {
        _httpClient = httpClient;
    }

    public async Task<string> MaskAsync(string text) {
        // Call Node.js Security Sidecar (security.ts)
        return text; 
    }

    public async Task<string> UnmaskAsync(string text) {
        return text;
    }
}
