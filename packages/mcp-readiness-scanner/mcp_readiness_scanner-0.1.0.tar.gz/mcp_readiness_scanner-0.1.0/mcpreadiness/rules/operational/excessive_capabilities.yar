/*
 * YARA Rules for Excessive Capabilities / Overloaded Scope
 *
 * These rules detect patterns suggesting a tool has too many
 * capabilities or an overly broad scope, which reduces reliability
 * and predictability.
 */

rule ManyCapabilities
{
    meta:
        title = "Many capabilities listed"
        description = "Tool definition lists many capabilities, indicating potential scope overload"
        category = "overloaded_scope"
        severity = "medium"
        remediation = "Consider splitting into focused single-purpose tools"

    strings:
        // Match capability arrays with many items (comma-separated patterns)
        $many_caps = /"capabilities"\s*:\s*\[[^\]]{200,}\]/
        $many_perms = /"permissions"\s*:\s*\[[^\]]{200,}\]/
        $many_scopes = /"scopes"\s*:\s*\[[^\]]{200,}\]/
        $many_actions = /"actions"\s*:\s*\[[^\]]{200,}\]/

    condition:
        any of them
}

rule KitchenSink
{
    meta:
        title = "Kitchen sink tool description"
        description = "Description suggests the tool does many unrelated things"
        category = "overloaded_scope"
        severity = "medium"
        remediation = "Split tool into focused components with clear responsibilities"

    strings:
        $and_more = "and more" nocase
        $and_much_more = "and much more" nocase
        $everything = "everything you need" nocase
        $all_in_one = "all-in-one" nocase
        $all_purpose = "all-purpose" nocase
        $multipurpose = "multi-purpose" nocase
        $swiss_army = "swiss army" nocase

    condition:
        any of them
}

rule VagueScope
{
    meta:
        title = "Vague scope description"
        description = "Tool description is vague about what it actually does"
        category = "overloaded_scope"
        severity = "low"
        remediation = "Provide specific, actionable description of tool capabilities"

    strings:
        $various_things = "various things" nocase
        $many_operations = "many operations" nocase
        $different_tasks = "different tasks" nocase
        $multiple_purposes = "multiple purposes" nocase
        $general_purpose = "general purpose" nocase
        $anything = "can do anything" nocase

    condition:
        any of them
}

rule TooManyVerbs
{
    meta:
        title = "Too many action verbs in description"
        description = "Description contains many action verbs suggesting overloaded scope"
        category = "overloaded_scope"
        severity = "info"
        remediation = "Focus on a single cohesive set of related operations"

    strings:
        // Common CRUD and action verbs appearing together
        $crud = /create.*read.*update.*delete/i nocase
        $manage_all = /manage.*monitor.*configure.*deploy/i nocase
        $do_all = /read.*write.*execute.*manage/i nocase

    condition:
        any of them
}

rule WildcardCapability
{
    meta:
        title = "Wildcard or 'all' capability"
        description = "Tool requests all or wildcard capabilities, indicating overly broad scope"
        category = "overloaded_scope"
        severity = "high"
        remediation = "Request only specific capabilities needed for the tool's function"

    strings:
        $wildcard_cap = /"capabilities"\s*:\s*\[\s*"\*"\s*\]/
        $all_cap = /"capabilities"\s*:\s*\[\s*"all"\s*\]/i
        $full_access = "full access" nocase
        $unrestricted = "unrestricted" nocase
        $admin = /"capabilities"[^]]*"admin"/i
        $superuser = "superuser" nocase

    condition:
        any of them
}

rule ManyParameters
{
    meta:
        title = "Many input parameters"
        description = "Tool has many input parameters suggesting complex or overloaded scope"
        category = "overloaded_scope"
        severity = "low"
        remediation = "Consider if all parameters are necessary or if the tool should be split"

    strings:
        // Match properties objects with many fields
        $many_props = /"properties"\s*:\s*\{[^}]{500,}\}/

    condition:
        any of them
}
