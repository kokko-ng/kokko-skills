# .NET Dead Code Detection

## Prerequisites

- .NET SDK 6.0+
- Roslynator.Analyzers when the solution already references it. Adding it is a project change: propose `dotnet add package Roslynator.Analyzers` in the report instead of running it during a check

## Analyzer Configuration (propose, do not apply)

The check runs the analyzers the solution already references. When these
settings are missing, put this block in the report for the user to adopt;
adding a package reference during a check is a project change:

```xml
<PropertyGroup>
  <EnableNETAnalyzers>true</EnableNETAnalyzers>
  <AnalysisLevel>latest-all</AnalysisLevel>
</PropertyGroup>

<ItemGroup>
  <!-- set Version to the current release on nuget.org -->
  <PackageReference Include="Roslynator.Analyzers" Version="<version>"
                    PrivateAssets="all" />
</ItemGroup>
```

## Commands

```bash
# Build with dead code warnings as errors
dotnet build \
  -warnaserror:CS0168,CS0169,CS0219,CS0414,IDE0051,IDE0052,IDE0059,IDE0060,CA1822

# Full analysis
dotnet build
```

## Key Analyzer Rules

- **CS0168** - Variable declared but never used
- **CS0169** - Field never used
- **CS0219** - Variable assigned but never used
- **CS0414** - Field assigned but never read
- **IDE0051** - Private member unused
- **IDE0052** - Private member unread
- **IDE0059** - Unnecessary value assignment
- **IDE0060** - Unused parameter
- **CA1822** - Member can be static (not using instance data)

## Check for Unused Dependencies

```bash
# List all package references
dotnet list package

# Check for deprecated packages
dotnet list package --deprecated

# Check for outdated packages
dotnet list package --outdated
```

## Verification Checklist

Verify each finding is unused before removing it; the analyzer cannot
see dynamic or convention-based use:

**Cross-check references:**

- All internal references across the solution
- Reflection-based access: `typeof()`, `nameof()`, `GetType()`
- Serialization attributes: `[JsonProperty]`, `[DataMember]`
- Dependency injection registrations
- Configuration binding targets
- Entity Framework navigation properties
- ASP.NET conventions (controllers, handlers)

**Check for indirect usage:**

- `dynamic` keyword usage
- `Activator.CreateInstance()`
- Assembly scanning (DI containers)
- Source generators
- Runtime compilation
- gRPC/SignalR contracts

## Removal Process

Once a finding is confirmed unused:

1. Remove the dead code
2. Create a separate commit:

   ```bash
   git add <the files you edited>
   git commit -m "chore(cleanup): remove unused <member>"
   ```

## Remove Unused Dependencies

```bash
dotnet remove package <package-name>
dotnet build
```

## Suppress False Positives

For code used via reflection or conventions:

```csharp
[System.Diagnostics.CodeAnalysis.SuppressMessage(
    "CodeQuality", "IDE0051",
    Justification = "Used by Entity Framework navigation")]
private ICollection<Order> Orders { get; set; }
```

## Commit Format

```text
chore(cleanup): remove unused <member>
```

## Final Quality Gate

```bash
dotnet build -warnaserror:CS0168,CS0169,IDE0051,IDE0052
```
