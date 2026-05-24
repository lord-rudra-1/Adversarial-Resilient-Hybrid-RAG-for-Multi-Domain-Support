# Claude for Education — LTI Integration Guide

## Overview

Claude can be integrated into Learning Management Systems (LMS) through the LTI (Learning Tools Interoperability) standard. This allows educators to embed Claude directly into their course workflows.

## Supported LMS Platforms

- Canvas
- Blackboard
- Moodle
- Brightspace (D2L)
- Google Classroom (via LTI bridge)

## Setup Process

### Prerequisites

1. An active Claude Team or Enterprise plan
2. LMS administrator access
3. An Anthropic API key with LTI scope

### Step 1: Request LTI Credentials

Contact Anthropic's education team at education@anthropic.com with:
- Your institution name
- LMS platform and version
- Expected number of users
- Primary use case

Anthropic will provide:
- LTI Consumer Key
- LTI Shared Secret
- Launch URL

### Step 2: Configure Your LMS

#### Canvas
1. Go to Settings > Apps > View App Configurations
2. Click "+ App"
3. Select "By URL" configuration type
4. Enter the Launch URL, Consumer Key, and Shared Secret
5. Enable "Send Institution Role" and "Send Email"
6. Save

#### Moodle
1. Go to Site Administration > Plugins > Activity Modules > External Tool
2. Click "Add Preconfigured Tool"
3. Enter the Launch URL and credentials
4. Set "Default Launch Container" to "Embed"
5. Save

### Step 3: Configure Usage Limits

Set per-student message limits to control API costs:
- Recommended: 50 messages/day for undergraduate courses
- Recommended: 100 messages/day for graduate courses
- Custom limits can be set per course section

### Step 4: Academic Integrity Settings

Configure Claude's behavior for educational contexts:
- **Socratic Mode**: Claude guides students toward answers rather than providing direct solutions
- **Source Requirement**: Require students to provide source material before Claude responds
- **Assignment Awareness**: Upload assignment instructions so Claude can detect and refuse to complete homework

## Pricing

Educational institutions receive a 40% discount on Claude Team pricing:
- Standard: $30/user/month → **$18/user/month** for education
- Minimum 20 seats for educational pricing
- Annual billing required

## Data Privacy

- Student data is never used for model training
- FERPA-compliant data handling
- Data residency options available (US, EU)
- SOC 2 Type II certified

## Support

- Education-specific support: education-support@anthropic.com
- Setup assistance: Schedule a call at calendly.com/anthropic-education
- Documentation: docs.anthropic.com/education
