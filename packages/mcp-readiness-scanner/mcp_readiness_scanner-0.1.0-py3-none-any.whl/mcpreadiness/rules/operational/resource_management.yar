/*
 * YARA Rules for Resource Management Issues
 *
 * These rules detect patterns indicating poor resource management
 * that could lead to memory leaks, connection exhaustion, or
 * resource starvation in production.
 */

rule MissingCleanup
{
    meta:
        title = "Missing resource cleanup"
        description = "Tool may not properly clean up resources like connections, files, or memory"
        category = "resource_leak"
        severity = "high"
        remediation = "Implement proper cleanup in finally blocks or context managers; ensure all resources are released"

    strings:
        $no_cleanup = "no cleanup" nocase
        $not_closed = "not closed" nocase
        $no_close = "no close" nocase
        $missing_cleanup = "missing cleanup" nocase
        $cleanup_skipped = "cleanup skipped" nocase
        $without_cleanup = "without cleanup" nocase
        $no_disposal = "no disposal" nocase
        $resources_not_freed = "resources not freed" nocase

    condition:
        any of them
}

rule ConnectionPooling
{
    meta:
        title = "Missing connection pooling or reuse"
        description = "Tool creates new connections without pooling, risking connection exhaustion"
        category = "resource_leak"
        severity = "medium"
        remediation = "Implement connection pooling and reuse for external services"

    strings:
        $new_connection = /creates?\s+new\s+connection/i nocase
        $no_pooling = "no connection pooling" nocase
        $without_pooling = "without pooling" nocase
        $pooling_disabled = "pooling disabled" nocase
        $no_reuse = "no connection reuse" nocase
        $fresh_connection = "fresh connection every time" nocase

    condition:
        any of them
}

rule MemoryLeak
{
    meta:
        title = "Potential memory leak"
        description = "Tool description suggests possible memory leak or unbounded growth"
        category = "resource_leak"
        severity = "critical"
        remediation = "Implement proper memory management; bound cache sizes; clean up references"

    strings:
        $memory_leak = "memory leak" nocase
        $leaks_memory = "leaks memory" nocase
        $unbounded_growth = "unbounded growth" nocase
        $unlimited_cache = "unlimited cache" nocase
        $cache_never_cleared = "cache never cleared" nocase
        $grows_indefinitely = "grows indefinitely" nocase
        $no_size_limit = "no size limit" nocase
        $accumulates_memory = "accumulates memory" nocase

    condition:
        any of them
}

rule FileHandleExhaustion
{
    meta:
        title = "File handle or descriptor leak"
        description = "Tool may leak file handles or descriptors"
        category = "resource_leak"
        severity = "high"
        remediation = "Use context managers or ensure explicit file closure; implement file handle limits"

    strings:
        $file_not_closed = "file not closed" nocase
        $open_files = "keeps files open" nocase
        $file_handle_leak = "file handle leak" nocase
        $fd_leak = "file descriptor leak" nocase
        $unclosed_files = "unclosed files" nocase
        $no_file_close = "doesn't close files" nocase
        $file_left_open = "file left open" nocase

    condition:
        any of them
}

rule UnboundedBuffer
{
    meta:
        title = "Unbounded buffer or queue"
        description = "Tool uses unbounded buffers or queues that may consume excessive memory"
        category = "resource_leak"
        severity = "high"
        remediation = "Set maximum buffer/queue sizes; implement backpressure mechanisms"

    strings:
        $unbounded_buffer = "unbounded buffer" nocase
        $unlimited_buffer = "unlimited buffer" nocase
        $unbounded_queue = "unbounded queue" nocase
        $unlimited_queue = "unlimited queue" nocase
        $no_buffer_limit = "no buffer limit" nocase
        $queue_grows = "queue grows without bound" nocase
        $infinite_buffer = "infinite buffer" nocase
        $no_backpressure = "no backpressure" nocase

    condition:
        any of them
}
