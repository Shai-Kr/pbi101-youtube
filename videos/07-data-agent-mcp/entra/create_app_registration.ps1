# One-time app registration for ChatGPT -> Fabric data agent MCP (az CLI, PowerShell).
# Run as someone who can create app registrations, in YOUR tenant:
#   az login --tenant <your-tenant>
# Then paste the Callback URL that ChatGPT shows (Plugins > Add > Add custom MCP server > Advanced OAuth settings).

$callback = "<paste ChatGPT's Callback URL here>"
$name     = "ChatGPT - data agent"

$body = @{
  displayName            = $name
  signInAudience         = "AzureADMyOrg"
  isFallbackPublicClient = $true
  publicClient           = @{ redirectUris = @($callback, "https://chatgpt.com/connector_platform_oauth_redirect") }
  requiredResourceAccess = @(
    @{ resourceAppId = "00000009-0000-0000-c000-000000000000"      # Power BI Service (Fabric)
       resourceAccess = @(
         @{ id = "c6756612-6853-4145-a661-90c1d045b2dc"; type = "Scope" },   # DataAgent.Execute.All
         @{ id = "40fa91d5-73ef-412c-a8c8-c8658670d0eb"; type = "Scope" },   # DataAgent.Read.All
         @{ id = "7f33e027-4039-419b-938e-2f8ca153e68e"; type = "Scope" }    # Dataset.Read.All
       ) },
    @{ resourceAppId = "00000003-0000-0000-c000-000000000000"      # Microsoft Graph
       resourceAccess = @( @{ id = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"; type = "Scope" } ) }   # User.Read
  )
} | ConvertTo-Json -Depth 6

$tmp = New-TemporaryFile
Set-Content -Path $tmp -Value $body -Encoding utf8
az rest --method post --url https://graph.microsoft.com/v1.0/applications --headers "Content-Type=application/json" `
        --body "@$tmp" --query "{name:displayName, clientId:appId}" -o table
Remove-Item $tmp
# Paste clientId into ChatGPT's "OAuth client ID". No secret. Consent happens at the first sign-in.
# (Permission ids are Microsoft's well-known ids; check them with:
#   az ad sp show --id 00000009-0000-0000-c000-000000000000 --query "oauth2PermissionScopes[?starts_with(value,'DataAgent')]")
