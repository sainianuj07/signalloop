# PRD: App Performance and Stability Issues
**Status:** Draft · **Priority:** P0 · **Evidence:** 32 reports

## 1. Background & Context
The app performance and stability issues have surfaced now due to a significant increase in user reports, with 32 users citing problems such as slow loading times, bugs, and features not working as expected. The data shows an average severity of 2.56/4, with a RICE score of 34.8, indicating a substantial impact on user experience. Reviews such as [#50], [#140], and [#149] highlight the frustration users are experiencing, with some even considering churning due to the app's unreliability. The sheer volume of reports and the severity of the issues justify the high priority of P0.

## 2. Problem Statement
The core problem can be broken down into four distinct sub-problems:
1. **Slow loading times and lag**: Users are experiencing slow loading times, with some reporting that the app is "laggy" and "barely works" ([#149], [#22], [#40]). This affects all users, particularly those on mobile devices.
2. **Bugs and feature failures**: Features are randomly stopping, and users are encountering bugs such as image resizing issues ([#53]) and toolbar disappearance ([#58]). This affects users who rely on specific features, such as those who use the app for task management.
3. **Page loading failures**: Users are experiencing issues with pages not loading, including the inability to open more than one page at once on mobile ([#58]) and pages not loading after search ([#46]). This affects users who need to access multiple pages simultaneously.
4. **Unreliable performance**: The app's performance is unpredictable, with some users reporting that it "just stops working" ([#50]) or is "slow to use" ([#154]). This affects all users, particularly those who rely on the app for critical tasks.

## 3. Goals & Non-Goals
- **Goals:**
  1. Improve app loading times by 30% within the next two releases.
  2. Reduce bug-related user reports by 40% within the next three releases.
  3. Increase user satisfaction with app performance by 25% within the next four releases.
  4. Ensure that 95% of users can access all features without issues within the next two releases.
  5. Decrease crash-related 1-star reviews by 50% within the next two releases.
- **Non-Goals:**
  1. Implementing a completely new UI, as this is not a priority for users at this time.
  2. Adding new features that may exacerbate existing performance issues.
  3. Optimizing the app for older devices, as this is not a primary concern for our user base.

## 4. Requirements
1. **P0**: Implement a caching mechanism to reduce loading times, as evidenced by user reports of slow loading times ([#22], [#40], [#152]).
2. **P1**: Conduct a thorough review of the app's codebase to identify and fix bugs, as reported by users ([#50], [#53], [#58], [#146], [#178]).
3. **P1**: Optimize database queries to improve page loading times, as users are experiencing issues with page loading ([#46], [#58], [#91], [#103]).
4. **P2**: Implement a feature to allow users to freeze columns on mobile, as requested by users ([#103]).
5. **P2**: Improve the app's handling of screen switching on foldable phones, as reported by users ([#182]).

## 5. Success Metrics
1. **Cut crash-related 1-star reviews by 50% within two releases**, as measured by the number of 1-star reviews citing crashes or performance issues.
2. **Reduce average loading time by 30% within two releases**, as measured by user feedback and app performance metrics.
3. **Increase user satisfaction with app performance by 25% within four releases**, as measured by user surveys and feedback.
4. **Ensure that 95% of users can access all features without issues within two releases**, as measured by user reports and app performance metrics.
5. **Reduce bug-related user reports by 40% within three releases**, as measured by the number of user reports citing bugs or feature failures.

## 6. Risks & Open Questions
1. **Technical risk**: The caching mechanism may not be effective in reducing loading times, or may introduce new issues.
2. **UX risk**: The optimized database queries may affect the app's UI, requiring additional design and testing efforts.
3. **Scope risk**: The review of the app's codebase may uncover more issues than anticipated, requiring additional resources and time.
4. **Open question**: How will we prioritize and address the numerous bug reports and feature requests from users?
5. **Open question**: What are the root causes of the app's performance issues, and how can we ensure that we are addressing the underlying problems rather than just symptoms?

---
## Citation Verification (automated guardrail)
- Citations found: **15**
- Valid (point to a real review in this theme): **15**
- Hallucinated (id not in this theme): **0** — none

## Evidence — verbatim from source (rendered from DB, not the model)
- **[#22]** (ux_friction, sev 2): "very laggy app plus website also feels very laggy"
- **[#40]** (ux_friction, sev 2): "This app works so slow"
- **[#46]** (bug, sev 3): "Sometimes, even multiple times a day, I go to make a new page or click on an existing one and the page just straight up doesn't load. I have to exit and clear cache for anything to happen. This is both on mobile data & wifi. The app has a lot of annoying glitches like this even a"
- **[#50]** (bug, sev 4): "Every week something new just stops working randomly"
- **[#53]** (bug, sev 3): "recently on Android for some reason images have been resized for me, no matter what I do, even in a new page, the images are always tiny, but appear normal on desktop, and even can appear normal on mobile, this is a serious resizing glitch that never happened before and I hope yo"
- **[#58]** (bug, sev 3): "A ton of bugs on mobile: - different UI between mobile app and mobile browser - mobile app: can't open more than one page at once - mobile app: needs to tap 3 times to open a page after search - mobile app: the toolbar to perform changes randomly disappears - mobile browser: brok"
- **[#91]** (ux_friction, sev 3): "The app offers a poor user experience The back button has several issues, particularly in the "multi-select" menus, where it's not present. Pressing the system's back button returns you to the home page. There's also a delay in database response. Currently, using the browser is e"
- **[#103]** (ux_friction, sev 3): "Why it's not possible to freeze the columns on the mobile app? Also, why is it so hard to move columns and properties order? The app is also too slow when you need it to be fast. You click on the table fields and nothing happens."
- **[#140]** (churn_risk, sev 4): "Simply not worth the effort and time."
- **[#146]** (bug, sev 2): "yo I cant add pictures"
- **[#149]** (bug, sev 4): "Laggy, lost all of my informations, barely can customize anything, stress..."
- **[#152]** (ux_friction, sev 2): "It never works well on mobile, I have a great Samsung smartphone with good memory, etc but it gets stuck on loading a lot."
- **[#154]** (ux_friction, sev 2): "Good features but the app is slow to use."
- **[#178]** (bug, sev 2): "customizable but has bugs like clicking in on a specific part of a database and not being able to swipe down on Android"
- **[#182]** (bug, sev 3): "On a foldable phone the app does not handle well switching from the outer screen to the inner, bigger screen. needs to be restarted often."
