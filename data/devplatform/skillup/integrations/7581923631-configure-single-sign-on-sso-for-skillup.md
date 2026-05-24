---
title: "Configure Single Sign-On (SSO) for SkillUp Prerequisites Configuring SSO for SkillUp"
title_slug: "configure-single-sign-on-sso-for-skillup-prerequisites-configuring-sso-for-skillup"
source_url: "https://support.devplatform.com/articles/7581923631-configure-single-sign-on-sso-for-skillup"
article_slug: "7581923631-configure-single-sign-on-sso-for-skillup"
last_updated_exact: "Nov 6, 2025, 1:02 AM"
last_updated_relative: "Last updated 6 months ago"
breadcrumbs:
  - "SkillUp"
  - "Integrations"
---

# Configure Single Sign-On (SSO) for SkillUp Prerequisites Configuring SSO for SkillUp

_Last updated: Nov 6, 2025, 1:02 AM (Last updated 6 months ago)_

SSO allows members of your organization to securely access SkillUp using their existing corporate credentials, eliminating the need for separate login details.

# Prerequisites

- You must have Company Admin access in your DevPlatform for Work account.

- Your organization must use a SAML 2.0-compliant Identity Provider (IdP), such as Okta, Azure AD, or OneLogin.

# Configuring SSO for SkillUp

SkillUp uses the same SSO configuration as DevPlatform for Work. To enable SSO for SkillUp, you must first configure it in your DevPlatform for Work account. 

**Note:** If your organization already uses SSO for DevPlatform for Work, skip **Step 1** and proceed to [Step 2: Provision users for SkillUp](https://support.devplatform.com/articles/7581923631-configure-single-sign-on-sso-for-skillup#step-2-provision-users-for-skillup-11).

To configure SSO for SkillUp:

## Step 1: Configure SSO in DevPlatform for Work

To configure SSO in DevPlatform for Work:

1.  Follow the [Getting Started with Single Sign-On (DevPlatform for Work)](https://support.devplatform.com/articles/4264962721-getting-started-with-single-sign-on) article to complete the initial configuration.

2.  Follow the appropriate SSO setup article based on your organization’s IdP:

    - [Okta](https://support.devplatform.com/articles/2841246365-setting-up-devplatform-single-sign-on-with-okta)

    - [Azure AD](https://support.devplatform.com/articles/3007497492-setting-up-devplatform-single-sign-on-with-azure-ad)

    - [OneLogin](https://support.devplatform.com/articles/6114369280-setting-up-devplatform-sso-with-onelogin)

Once you complete the SSO configuration, all users under the same verified domain automatically authenticate to SkillUp using SSO.

## Step 2: Provision users for SkillUp

You can provision users for SkillUp in two ways:

### Manual provisioning

Admins can manually invite users directly from the SkillUp Admin Panel. For more information, see [](https://support.devplatform.com/articles/3868789028-user-management) [📄 User Management](/articles/3868789028).

### Automated provisioning with SCIM

You can automate user provisioning in SkillUp using the System for Cross-domain Identity Management (SCIM) protocol. SCIM automatically creates, updates, and deactivates SkillUp user accounts based on changes in your organization’s directory.

This method is recommended for organizations that use SCIM 2.0 compliant IdPs such as Okta, Azure AD, or OneLogin.

To set up SCIM, use one of the following options based on your organization’s configuration:

- **First-time setup:** If you are setting up SCIM with DevPlatform for the first time, follow the [Setting Up SCIM Provisioning for SkillUp](https://support.devplatform.com/articles/9005750838-setting-up-scim-provisioning-for-skillup?lang=en) article.

- **Existing SCIM setup for DevPlatform for Work:** If your organization already uses SCIM for DevPlatform for Work, you can reuse the same SCIM endpoint and authentication token for SkillUp.This setup automatically synchronizes both platforms.\
  If your existing SCIM configuration uses Okta, follow the instructions in the [Extend SCIM Provisioning with Okta to SkillUp](https://support.devplatform.com/articles/9570265682-extend-scim-provisioning-with-okta-to-skillup?lang=en) article to ensure the correct functioning of SCIM for SkillUp.

## Step 3: Access SkillUp

Users can access SkillUp either via their IDP tool or by visiting [devplatform.com/skillup/home](http://devplatform.com/skillup/home) and logging in. 

If a user has access to both SkillUp and DevPlatform for Work, logging in through the IdP redirects them to the DevPlatform for Work home page. They can access SkillUp from the **App Switcher** in the top navigation bar.

![HRWtoSkillUp.gif](https://assets.usepylon.com/e6a58e21-be80-4777-9eaf-f73beeee94d9%2F1762353738568-HRWtoSkillUp.gif?Expires=253370764800&Signature=uqGiLFsMUMEMtxv5gDIj4-85E5C7qj3t27KpoYTiCpLyHYdHR5VnA9289flWKbQx95vQLJQGfnb0vWqDYy0mIij6Uis1OHyPsEZGMFwqX1cddfzfpC0YNFjUgY00PcKKsFqHA2vNw8V-pI~FvvSl3hpULEgxbIBjjEzd8pnpPiXRPbBKDu9-qktIqZQGdoNDWS2W9nHUYsnDp3mCUT4ccWrxIt7Ub5NgowQg6KsnSVlXA8-wQtg0P5udZ~dc8zg-JJppYz1ASUEVr9HSJgoaLSXjVFcOzzoVomZbDawby1TU4N~5BXjEiT30JKXiH6HOyb~vPGBTNMhkn~H77WLAEg__&Key-Pair-Id=K3NV4LZ47N8M46)

**Note:** Users may temporarily lose access for up to 2 hours during the transition from regular login to SSO.

For assistance in configuring SSO, contact your DevPlatform Account Manager or email [skillup-support@devplatform.com](mailto:skillup-support@devplatform.com).

\

\
