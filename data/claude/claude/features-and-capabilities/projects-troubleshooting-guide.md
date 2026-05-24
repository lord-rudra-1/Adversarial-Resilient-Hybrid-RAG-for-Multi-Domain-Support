# Claude Projects Feature — Troubleshooting Guide

## Common Issues

### Project Instructions Not Being Followed

If Claude doesn't seem to follow your Project Instructions:

1. **Check your plan**: Projects are only available on Claude Pro, Team, and Enterprise plans
2. **Verify instructions are saved**: Click the Project name, go to Settings, and confirm instructions are there
3. **Instruction length**: Instructions are limited to 10,000 characters. If you exceed this, only the first 10,000 characters are used
4. **New conversations**: Project instructions apply only to **new conversations** started within the project. Existing conversations are not retroactively updated
5. **Instruction conflicts**: If your message contradicts the project instructions, Claude will try to follow both but may prioritize your direct message

### Known Limitations

- Projects are not available on the free plan
- Project-level knowledge (uploaded files) has a limit of 200,000 tokens per project
- Files uploaded to a project are shared across all conversations in that project
- Project instructions do not override Claude's core safety training
- Projects cannot be shared between individual accounts (only Team/Enterprise)

### Steps to Verify

1. Create a **new** conversation within the project (don't reuse an old one)
2. Start with a simple test: ask Claude to follow a specific instruction from your project settings
3. If it works in a new conversation but not old ones, this is expected behavior
4. If it doesn't work in new conversations either, try:
   - Reducing instruction length
   - Simplifying instruction language
   - Removing contradictory instructions
   - Logging out and back in

## How Project Instructions Work

Project Instructions are prepended to the system prompt for every conversation within the project. They function similarly to custom instructions but are scoped to a specific project.

Priority order (highest to lowest):
1. Claude's core safety and helpfulness training
2. Organization-level settings (Team/Enterprise)
3. Project Instructions
4. User's message in the current conversation

## Related Articles

- [Creating and Managing Projects](/articles/projects-overview)
- [Uploading Files to Projects](/articles/project-files)
- [Project Sharing and Permissions](/articles/project-sharing)
