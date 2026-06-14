# PRD: Functionality & Usability Issues
**Status:** Draft · **Priority:** P1 · **Evidence:** 15 reports

## 1. Background & Context
The recent surge in user reports highlights significant functionality and usability issues with our mobile app, which have led to a poor user experience. The data shows that 15 users have reported issues, with an average severity of 2.87/4 and a RICE score of 19.4. Users like [#56] and [#189] have expressed frustration with the app's lag, bugs, and lack of basic stability, leading to content loss and app freezing. Others, like [#24] and [#35], have reported difficulties with content vanishing automatically and issues with scrolling and popup windows. These problems have been persistent, with some users, like [#39], experiencing issues with voice dictation and input gargling. The sheer volume of reports and the severity of the issues warrant immediate attention.

## 2. Problem Statement
The core problem can be broken down into four distinct sub-problems:
1. **Lag and performance issues**: The app is slow to respond, and users experience significant lag, making it difficult to perform basic actions. This affects users like [#56] and [#132], who have reported that the app is "extremely laggy" and "jaggy."
2. **Bugs and crashes**: The app is prone to bugs and crashes, leading to content loss and frustration. Users like [#189] and [#183] have reported issues with copying and pasting content, and accidental deletions that cannot be undone.
3. **Unintuitive interface**: The app's interface is not user-friendly, making it difficult for users to perform simple tasks. Users like [#62] and [#88] have reported issues with editing and highlighting text, and navigating the app's features.
4. **Voice dictation issues**: The app's voice dictation feature is not functioning correctly, leading to input gargling and incorrect text input. Users like [#39] and [#165] have reported issues with voice dictation, including incorrect word recognition and formatting issues.

## 3. Goals & Non-Goals
- **Goals:**
  1. Improve the app's performance and responsiveness to reduce lag and crashes.
  2. Fix bugs and crashes to prevent content loss and frustration.
  3. Simplify the app's interface to make it more intuitive and user-friendly.
  4. Enhance the voice dictation feature to improve accuracy and functionality.
  5. Reduce user frustration and churn risk by addressing the root causes of these issues.
- **Non-Goals:**
  1. Redesigning the app's overall architecture or rewriting the codebase from scratch.
  2. Adding new features or functionality that are not directly related to addressing the current issues.
  3. Conducting a comprehensive user research study to inform the design of the app.

## 4. Requirements
1. **P0**: Fix the bug that causes content to vanish automatically, as reported by users like [#24] and [#35].
2. **P1**: Optimize the app's performance to reduce lag and crashes, as reported by users like [#56] and [#132].
3. **P1**: Improve the app's interface to make it more intuitive and user-friendly, as reported by users like [#62] and [#88].
4. **P1**: Enhance the voice dictation feature to improve accuracy and functionality, as reported by users like [#39] and [#165].
5. **P2**: Implement a more robust undo and redo system to prevent accidental deletions, as reported by users like [#183].

## 5. Success Metrics
1. **Reduce crash-related 1-star reviews by 50% within two releases**, as measured by the number of 1-star reviews that mention crashes or bugs.
2. **Increase user satisfaction with the app's performance by 30% within three releases**, as measured by user surveys and feedback.
3. **Decrease the average time it takes for users to complete basic tasks by 25% within two releases**, as measured by user testing and feedback.
4. **Improve the voice dictation feature's accuracy by 40% within two releases**, as measured by user testing and feedback.
5. **Reduce user churn risk by 20% within three releases**, as measured by the number of users who report issues with the app.

## 6. Risks & Open Questions
1. **Technical risk**: The app's codebase may be more complex than anticipated, making it difficult to identify and fix the root causes of the issues.
2. **UX risk**: The simplified interface may not meet the needs of all users, potentially leading to further frustration and churn.
3. **Scope risk**: The requirements may not fully address the underlying issues, leading to further problems down the line.
4. **Open question**: How will we measure the success of the voice dictation feature's enhancements, and what metrics will we use to evaluate its accuracy and functionality?
5. **Open question**: What is the root cause of the content vanishing issue, and how can we ensure that it is fully addressed and prevented in the future?

---
## Citation Verification (automated guardrail)
- Citations found: **10**
- Valid (point to a real review in this theme): **10**
- Hallucinated (id not in this theme): **0** ✅ none

## Evidence — verbatim from source (rendered from DB, not the model)
- **[#24]** (bug, sev 3): "Many difficulties, Content vanished automatically."
- **[#35]** (bug, sev 3): "On a page block the background colour menu doesn't scroll, popup window is frozen. Also the Action menu is frozen and won't swipe down. Samsung galaxy s20"
- **[#39]** (bug, sev 3): "Great app. One big problem. A few months ago it started gargling input when using voice dictation. For me this is a serious degradation in usability. Upgrades haven't helped."
- **[#56]** (bug, sev 4): "The PC version is excellent, but the mobile app has become a disaster after the recent updates. It is extremely laggy, full of bugs, and lacks basic stability. It feels like the mobile version is completely neglected compared to the desktop. It needs serious optimization and imme"
- **[#62]** (ux_friction, sev 3): "it's so hard to edit especially on mobile, every time I go to next line it's going to next block, and when it's list it's going the same, and some aren't list is not going to next block. it's like so messy and hard to control. so badddd app fr, don't download it if you don't want"
- **[#88]** (ux_friction, sev 2): "Absolutely not userfrendly app, 15 minutes try to understand where to pres and what to do to crate a note."
- **[#132]** (bug, sev 3): "laggy, bug: app is jaggy and ignoring steps when pasting (only delete the text without replacing it with the text paste)"
- **[#165]** (bug, sev 3): "whenever I use voice type, it always jumps onto the word before and makes a cursed word. like Muhammad Ali turns into IcMuhammuhammadmuhammad. this only happens whenever I change the font, (bold,italic etc.)or at the start of a new paragraph. it only happens on this app not any o"
- **[#183]** (bug, sev 3): "Really great potential but there's just so many bugs. The worst one so far is when something gets accidentally deleted (sometimes my fault, sometimes it's the app), I can't even undo it. For example, I cut a whole table column but when I tried to paste it, it didn't paste anythin"
- **[#189]** (churn_risk, sev 4): "cant copy anything, deletes my notes if I leave screen. sucks. moving away"
