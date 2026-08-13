# Sachkov Inside — confirmed intake

Status: shared understanding confirmed on 2026-08-13. This file is the pre-harness intake,
not an application specification.

## Purpose of this repository

This is the private control plane for the paid engineering Membership: product strategy,
launch and community operations, content portfolio, research, decisions, roadmaps and links to
authoritative artifacts.

It is not the repository of the future Membership application. Kirill will create that product
from scratch during the member-only build series after its product decisions are made in the
series itself.

## Confirmed product picture

- Launch the Membership Telegram-first as a monthly paid subscription open to the whole current
  audience, not a capped founding cohort.
- Initial delivery uses a private Telegram channel plus a community chat. Tribute is a candidate
  for subscription and access automation, subject to a separate evidence-based check.
- The Membership is an engineering community for developers who already program in any language.
  Its center is web/fullstack engineering: backend, frontend, architecture, infrastructure,
  some DevOps, and a strong AI-first focus.
- The offer includes Kirill's practical guides and experience, work with AI agents, development
  of a new product from zero, career and job-search guidance, discussion, answers in chat,
  occasional reviews and streams. Kirill participates actively but there is no response-time SLA
  or personal mentoring guarantee.
- Knowledge is organized by direction and entry level rather than one linear course for everyone.
- Full videos, guides, artifacts and discussion stay inside Membership; public channels receive
  teasers and selected conclusions.
- Launch requires a kickoff pack: manifesto/roadmap, rules, several cornerstone guides and the
  first episode of the build series.
- Each build-series milestone contains a video, structured guide, decision artifacts and linked
  code/design evidence. Members receive read-only access to the private live repository.
- Telegram remains the community and short-announcement layer. The future application becomes
  the home for materials and related workflows.

## Intentionally deferred into the build series

- Public product name; current direction is something around `Inside`.
- Future application MVP and workflows.
- Future application billing and Membership authority.
- Stack, architecture, design system, infrastructure and repository creation for the application.

These are not missing requirements for the Telegram-first launch. They are deliberate episodes
and owner decisions in the series.

## Repository boundaries

- This repository owns Membership strategy, product and operational decisions, content pillars,
  portfolio/backlog, research, launch evidence and cross-project links.
- `sachkov-content` owns production artifacts: scripts, videos, lessons, posts and publication
  workflow. Do not duplicate those artifacts here.
- `education-platform` issue #1108 remains an independent backlog initiative. This project does
  not replace or rewrite it.
- No payment activation, invitations, publication, external messages or production mutation
  without an explicit owner GO.

## Next route

Bootstrap a project harness with the `content` stack and private GitHub Issues tracker, then create
a Wayfinder Map. The first sharp work should validate the Telegram/Tribute launch boundary,
resolve the initial commercial and naming decisions, define the kickoff content floor, and map the
handoff into `sachkov-content` without specifying the future application prematurely.
