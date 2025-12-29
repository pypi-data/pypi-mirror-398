# AGENTS.md


<!-- skilz:skills:start -->

## Installed Skills

The following skills are available (managed by skilz):

- **test-skill**: `/test-skill` - test/skill
- **test-skill**: test/skill

<!-- skilz:skills:end -->

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills
below can help complete the task more effectively.

How to use skills:
- Invoke: Bash("skilz read <skill-name>")
- The skill content will load with detailed instructions
- Base directory provided in output for resolving bundled resources

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
</usage>

<available_skills>

<skill>
<name>docs-seeker</name>
<description>Search technical documentation using executable scripts to detect query type, fetch from llms.txt sources (context7.com), and analyze results. Use when user needs: (1) Topic-specific documentation (features/components/concepts), (2) Library/framework documentation, (3) GitHub repository analysis, (4) Documentation discovery with automated agent distribution strategy</description>
<location>.claude/skills/docs-seeker/SKILL.md</location>
</skill>

<skill>
<name>my-skill</name>
<description>Skill: local/my-skill</description>
<location>/var/folders/tm/chrvt43s3rbdld20ghw1qtc40000gn/T/tmp36jvsujy/.claude/skills/my-skill/SKILL.md</location>
</skill>

<skill>
<name>test-skill</name>
<description>Skill: test/skill</description>
<location>/var/folders/tm/chrvt43s3rbdld20ghw1qtc40000gn/T/tmpxfgj27gb/.claude/skills/test-skill/SKILL.md</location>
</skill>

<skill>
<name>web-artifacts-builder</name>
<description>Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.</description>
<location>.claude/skills/web-artifacts-builder/SKILL.md</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
