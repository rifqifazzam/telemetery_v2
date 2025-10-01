# Research & Solve Command

This command provides comprehensive research and problem-solving capabilities by leveraging available MCP tools and resources.

## Instructions

When using this command, you must:

1. **Utilize Available MCPs**:
   - Always search for latest documentation using `context7` MCP for library documentation
   - Use `web-search-prime` MCP for current web information when needed
   - Leverage `playwright` MCP for testing web functionalities when applicable

2. **Research Approach**:
   - Start with `context7` for library-specific documentation and examples
   - Use `web-search-prime` for general web searches and recent information
   - Test functionalities with `playwright` when web-related features are implemented
   - Verify solutions work before declaring task completion

3. **Problem Solving**:
   - For complex issues: Use `web-search-prime` to search for solutions online
   - Combine with `WebFetch` to get detailed information from specific URLs
   - Test implementations thoroughly before considering tasks done
   - Document findings and solutions

4. **Best Practices**:
   - Always verify the latest documentation before implementing
   - Test web functionalities using playwright when possible
   - Search for solutions to difficult problems using available web tools
   - Ensure all tested features work as expected
   - Provide comprehensive solutions with proper testing

## Usage Examples

```
/rs research asyncio best practices
/rs solve connection timeout issue
/rs test web application functionality
```

## Command Variables

- `$1`: Task description or research topic
- `$ARGUMENTS`: All arguments passed to the command

Use this command when you need thorough research, documentation lookup, web testing, or complex problem solving with verified solutions.