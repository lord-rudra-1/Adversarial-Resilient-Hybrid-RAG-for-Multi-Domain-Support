---
title: "Ashby - DevPlatform Technical Interview Integration Guide"
title_slug: "ashby-devplatform-technical-interview-integration-guide"
source_url: "https://support.devplatform.com/articles/7862793608-ashby-devplatform-technical-interview-integration-guide"
article_slug: "7862793608-ashby-devplatform-technical-interview-integration-guide"
last_updated_exact: "Jun 5, 2025, 6:03 PM"
last_updated_relative: "Last updated 11 months ago"
breadcrumbs:
  - "Integrations"
  - "Applicant Tracking Systems"
  - "Ashby"
---

# Ashby - DevPlatform Technical Interview Integration Guide

_Last updated: Jun 5, 2025, 6:03 PM (Last updated 11 months ago)_

This article explains how to configure and use the DevPlatform - Ashby integration to send **technical interviews** via DevPlatform's Interview product directly from Ashby. Once the setup is complete, recruiters and coordinators can attach live coding interview links when scheduling interviews and track interview activity within Ashby.

## Prerequisites

|  |  |
|----|----|
| **In DevPlatform** | **In Ashby** |
| Pricing plan with Interview access | Admin user account with permissions to manage integrations |
| Recruiter license | Email address must match DevPlatform for Work account |

## Configuring the Integration

![Ashby_Interviews.gif](https://assets.usepylon.com/e6a58e21-be80-4777-9eaf-f73beeee94d9%2F1749126769422-Ashby_Interviews.gif?Expires=253370764800&Signature=QOckradUwW3VvLeZSBSyBPEjehUEV-igE5vjsQJ6WDh6GdzESCViqsWRgvv47JRvjoZU12F4HEydESKy04D2pDh4BvNgBcJjNYFuo9dxbIrrC0uzb82vEzi9CkgfOnkOTIdrj5PiA0Wy~vp0oVBmT1OGxDncGzNxB199iyJHP6uNyqWDAec4Bj18wT1iWbYlV4sbDtANUQnm-PhpovzupOfG5QWQ1auj2RZPZM3O~XZdyUOWEu7DMOzfRSbUCgS7c5A5gKyW0J4PcKzma7-MBO2tO5-plPps8SI3O5XHygIrugqdwu-Y-ZhNxDfxAABeyvSN0Wi1GOT7eruOFRMfAQ__&Key-Pair-Id=K3NV4LZ47N8M46)

### Step 1: Enable Integration in Ashby

1.  Log in to [Ashby Integrations Marketplace](https://app.ashbyhq.com/admin/integrations/marketplace).

2.  Locate the **DevPlatform** tile and click **Enable DevPlatform**.

3.  Under **Configuration**:

    - Select or create an Ashby API key.

    - The key must have write access to the **Candidates** endpoints (specifically, `assessment.update`).

### Step 2: Generate DevPlatform API Key

1.  Log in to **DevPlatform for Work** using Company Admin account..

2.  Go to the **Settings \> Integrations**.

3.  Locate the **Ashby** integration tile and click **Configure**.

4.  Click **Generate API Token**.

5.  Copy the token immediately. You will not be able to retrieve it later.

### Step 3: Add DevPlatform API Key to Ashby

1.  Return to the **Ashby DevPlatform integration** panel.

2.  Paste the **DevPlatform API token** into the designated field.

3.  Click **Test API Key** to validate.

4.  Select **DevPlatform** as the integration partner.

5.  Click **Create API Key** to complete the setup.

## Sending a DevPlatform Interview Link

Ashby allows you to include a DevPlatform **Live Interview** link when scheduling interviews.

To attach a live interview link:

1.  Go to the **Job** \> **Interview Plan**.

2.  Click **Schedule Interview** for a candidate.

3.  Under the **Communications** tab, toggle **Attach a DevPlatform Interview?** to **On**.

The generated interview link will be:

- Sent to both interviewer and candidate in their invite.

- Logged on the candidate’s activity timeline.

\

\
