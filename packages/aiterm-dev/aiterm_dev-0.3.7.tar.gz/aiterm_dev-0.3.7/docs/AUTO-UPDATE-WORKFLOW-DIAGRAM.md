# Documentation Auto-Update Workflow Diagram

This document contains visual workflow diagrams for the auto-update system.

---

## High-Level System Overview

```mermaid
graph TB
    subgraph "Your Workflow"
        A[Code & Commit] --> B[Run /workflow:done]
    end

    subgraph "Phase 2: Auto-Updates"
        B --> C{Detect Issues}
        C --> D[CHANGELOG<br/>missing entries?]
        C --> E[mkdocs.yml<br/>orphaned docs?]
        C --> F[.STATUS<br/>needs update?]

        D -->|Yes| G[update-changelog.sh]
        E -->|Yes| H[update-mkdocs-nav.sh]
        F -->|Yes| I[update-claude-md.sh]

        G --> J[Auto-apply<br/>CHANGELOG]
        H --> K[Auto-apply<br/>mkdocs.yml]
        I --> L[Prompt user<br/>.STATUS update]

        J --> M[Validate mkdocs build]
        K --> M
        L --> M

        M -->|Success| N[Show diff]
        M -->|Fail| O[Auto-rollback]

        N --> P[Commit changes?]
        O --> Q[Restore backups]

        P -->|Yes| R[Documentation<br/>updated!]
        P -->|No| S[Manual review]
    end

    R --> T[Done! ✓]
    S --> T
    Q --> T

    style A fill:#e1f5ff
    style B fill:#fff4e6
    style R fill:#d4edda
    style T fill:#d4edda
    style O fill:#f8d7da
    style Q fill:#f8d7da
```

---

## Detailed Update Flow

```mermaid
flowchart TD
    Start([User runs<br/>/workflow:done]) --> Detect[Step 1.6:<br/>Run all updaters]

    Detect --> Phase1[Phase 1: Detection]

    subgraph "Phase 1: Detect Documentation Issues"
        Phase1 --> CheckCL{Uncommitted<br/>commits?}
        Phase1 --> CheckMK{Orphaned<br/>docs?}
        Phase1 --> CheckST{.STATUS<br/>outdated?}

        CheckCL -->|Yes| FoundCL[Mark: CHANGELOG<br/>needs update]
        CheckMK -->|Yes| FoundMK[Mark: mkdocs.yml<br/>needs update]
        CheckST -->|Yes| FoundST[Mark: .STATUS<br/>needs update]

        CheckCL -->|No| SkipCL[Skip CHANGELOG]
        CheckMK -->|No| SkipMK[Skip mkdocs]
        CheckST -->|No| SkipST[Skip .STATUS]
    end

    FoundCL --> Phase2
    FoundMK --> Phase2
    FoundST --> Phase2
    SkipCL --> Phase2
    SkipMK --> Phase2
    SkipST --> Phase2

    subgraph "Phase 2: Safe Auto-Updates"
        Phase2[Auto-update<br/>safe files]

        Phase2 --> BackupCL[Backup<br/>CHANGELOG.md]
        Phase2 --> BackupMK[Backup<br/>mkdocs.yml]

        BackupCL --> UpdateCL[Parse commits<br/>Generate entries]
        BackupMK --> UpdateMK[Find orphaned docs<br/>Infer sections]

        UpdateCL --> AppendCL[Append to<br/>CHANGELOG]
        UpdateMK --> AppendMK[Add to<br/>mkdocs.yml nav]
    end

    AppendCL --> Phase3
    AppendMK --> Phase3

    subgraph "Phase 3: Interactive Updates"
        Phase3[Prompt for<br/>.STATUS update]

        Phase3 --> AskUser{User wants<br/>.STATUS update?}

        AskUser -->|Yes| BackupST[Backup .STATUS]
        AskUser -->|No| SkipSTUpdate[Skip .STATUS]

        BackupST --> GenSummary[Generate summary<br/>from git log]
        GenSummary --> UpdateST[Prepend to<br/>.STATUS]
    end

    UpdateST --> Validate
    SkipSTUpdate --> Validate

    subgraph "Phase 4: Validation"
        Validate[Validate changes]

        Validate --> BuildTest{mkdocs build<br/>--strict}

        BuildTest -->|Success| ShowDiff[Show git diff]
        BuildTest -->|Fail| Rollback[Rollback mkdocs.yml]

        Rollback --> RestoreBackup[Restore from<br/>.backup file]
        RestoreBackup --> Error[Error: Build failed]

        ShowDiff --> CommitPrompt{Commit<br/>changes?}

        CommitPrompt -->|Yes| GitCommit[git commit -m<br/>docs: auto-update]
        CommitPrompt -->|No| Manual[Manual review]
    end

    GitCommit --> Success([Success!<br/>Docs updated])
    Manual --> Success
    Error --> Success

    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style Error fill:#f8d7da
    style Phase2 fill:#fff4e6
    style Phase3 fill:#ffe6f0
    style Validate fill:#f0f0f0
```

---

## Individual Updater: CHANGELOG Flow

```mermaid
flowchart LR
    Start([update-changelog.sh]) --> Input[Input:<br/>Git commits]

    Input --> LastUpdate[Find last<br/>CHANGELOG commit]

    LastUpdate --> Range[Get commit range:<br/>last..HEAD]

    Range --> Parse{For each<br/>commit}

    Parse --> ConvCheck{Conventional<br/>format?}

    ConvCheck -->|Yes| Extract[Extract:<br/>type, scope, subject]
    ConvCheck -->|No| Warn[Mark as<br/>non-conventional]

    Extract --> TypeMap{Map type to<br/>section}
    Warn --> TypeMap

    TypeMap --> Added[feat → Added]
    TypeMap --> Fixed[fix → Fixed]
    TypeMap --> Changed[refactor/perf → Changed]
    TypeMap --> Docs[docs → Documentation]
    TypeMap --> Tests[test → Tests]
    TypeMap --> Build[build → Build System]
    TypeMap --> CI[ci → CI/CD]
    TypeMap --> Skip[chore/style → Skip]

    Added --> Format
    Fixed --> Format
    Changed --> Format
    Docs --> Format
    Tests --> Format
    Build --> Format
    CI --> Format

    subgraph "Formatting"
        Format[Format entry:<br/>- **scope**: subject]
        Format --> Link[Add GitHub<br/>commit link]
        Link --> Group[Group by<br/>section]
    end

    Group --> Check{--apply<br/>flag?}

    Check -->|No| Preview[Show preview<br/>Exit]
    Check -->|Yes| Backup[Create backup:<br/>.backup-YYYYMMDD]

    Backup --> Insert[Insert after<br/>[Unreleased]]

    Insert --> Save[Save CHANGELOG.md]

    Preview --> End([Done])
    Save --> End

    style Start fill:#e1f5ff
    style End fill:#d4edda
    style Preview fill:#fff4e6
    style Backup fill:#ffe6f0
```

---

## Individual Updater: mkdocs Navigation Flow

```mermaid
flowchart TD
    Start([update-mkdocs-nav.sh]) --> FindDocs[Find all .md files<br/>in project]

    FindDocs --> Filter{Filter files}

    Filter --> Exclude[Exclude:<br/>README, BRAINSTORM,<br/>*.backup-*, temp files]

    Exclude --> ReadNav[Read current<br/>mkdocs.yml nav]

    ReadNav --> Compare{For each<br/>doc file}

    Compare --> InNav{Already in<br/>navigation?}

    InNav -->|Yes| Skip[Skip file]
    InNav -->|No| Orphan[Mark as orphaned]

    Orphan --> InferSection{Infer section<br/>from filename}

    InferSection --> API[*API* → Reference]
    InferSection --> ARCH[*ARCHITECTURE* → Reference]
    InferSection --> GUIDE[*GUIDE* → User Guide]
    InferSection --> INTEG[*INTEGRATION* → User Guide]
    InferSection --> TUT[*TUTORIAL* → Tutorials]
    InferSection --> QUICK[*QUICKSTART* → Getting Started]
    InferSection --> PHASE[*PHASE* → Development]
    InferSection --> DESIGN[*DESIGN* → Development]
    InferSection --> Fallback[Fallback → Miscellaneous]

    API --> Extract
    ARCH --> Extract
    GUIDE --> Extract
    INTEG --> Extract
    TUT --> Extract
    QUICK --> Extract
    PHASE --> Extract
    DESIGN --> Extract
    Fallback --> Extract

    subgraph "Extract Title"
        Extract[Read first 5 lines]
        Extract --> FindH1{Find # heading}
        FindH1 -->|Yes| UseH1[Use heading text]
        FindH1 -->|No| UseFile[Use filename]
    end

    UseH1 --> Format
    UseFile --> Format

    subgraph "Format Entry"
        Format[Format:<br/>- Title: path/file.md]
    end

    Format --> Collect[Collect all<br/>new entries]

    Collect --> Check{--apply<br/>flag?}

    Check -->|No| Preview[Show preview<br/>Exit]
    Check -->|Yes| Backup[Create backup:<br/>mkdocs.yml.backup]

    Backup --> AddEntries[Add entries to<br/>appropriate sections]

    AddEntries --> Validate[Validate YAML<br/>syntax]

    Validate -->|Valid| Save[Save mkdocs.yml]
    Validate -->|Invalid| Restore[Restore backup<br/>Show error]

    Save --> BuildTest[Test: mkdocs build<br/>--strict]

    BuildTest -->|Pass| Success([Success!])
    BuildTest -->|Fail| Rollback[Rollback to backup<br/>Show error]

    Preview --> End([Done])
    Restore --> End
    Rollback --> End
    Success --> End

    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style End fill:#d4edda
    style Preview fill:#fff4e6
    style Backup fill:#ffe6f0
    style Restore fill:#f8d7da
    style Rollback fill:#f8d7da
```

---

## Individual Updater: .STATUS Update Flow

```mermaid
flowchart LR
    Start([update-claude-md.sh]) --> FindFile{Find status<br/>file}

    FindFile --> CheckStatus[Check .STATUS]
    FindFile --> CheckClaude[Check CLAUDE.md]

    CheckStatus -->|Found| UseStatus[Use .STATUS]
    CheckClaude -->|Found| UseClaude[Use CLAUDE.md]
    CheckStatus -->|Not found| CheckClaude
    CheckClaude -->|Not found| Error[Error: No file]

    UseStatus --> Input
    UseClaude --> Input

    subgraph "Gather Input"
        Input[Choose input<br/>method]

        Input --> CustomCheck{Custom<br/>--session arg?}

        CustomCheck -->|Yes| Custom[Use custom<br/>summary]
        CustomCheck -->|No| Auto[Auto-generate<br/>from git]

        Auto --> GitLog[Get recent<br/>commits]
        GitLog --> Stats[Get changed<br/>files stats]
        Stats --> GenSummary[Format:<br/>- commits<br/>- files<br/>- messages]
    end

    Custom --> Format
    GenSummary --> Format

    subgraph "Format Entry"
        Format[Format entry:<br/>✅ Session Completion<br/>+ date<br/>+ summary]

        Format --> UpdateFields[Update fields:<br/>updated: date<br/>progress: %]
    end

    UpdateFields --> Check{--apply<br/>flag?}

    Check -->|No| Preview[Show preview<br/>Exit]
    Check -->|Yes| Backup[Create backup:<br/>.STATUS.backup]

    Backup --> FindSection{Find section:<br/>## ✅ Just Completed}

    FindSection -->|Found| Prepend[Prepend new entry<br/>to section]
    FindSection -->|Not found| Create[Create section<br/>+ entry]

    Prepend --> Save[Save file]
    Create --> Save

    Preview --> End([Done])
    Save --> End
    Error --> End

    style Start fill:#e1f5ff
    style End fill:#d4edda
    style Preview fill:#fff4e6
    style Backup fill:#ffe6f0
    style Error fill:#f8d7da
```

---

## Safety & Rollback Flow

```mermaid
flowchart TD
    Start([Updater starts]) --> Backup[Create timestamped<br/>backup files]

    Backup --> B1[CHANGELOG.md.backup-<br/>YYYYMMDD-HHMMSS]
    Backup --> B2[mkdocs.yml.backup-<br/>YYYYMMDD-HHMMSS]
    Backup --> B3[.STATUS.backup-<br/>YYYYMMDD-HHMMSS]

    B1 --> Update
    B2 --> Update
    B3 --> Update

    subgraph "Update Process"
        Update[Make changes<br/>to files]

        Update --> Validate{Validation}

        Validate --> YAMLCheck[YAML syntax<br/>valid?]
        Validate --> BuildCheck[mkdocs build<br/>passes?]

        YAMLCheck -->|Pass| BuildCheck
        YAMLCheck -->|Fail| RollbackYAML

        BuildCheck -->|Pass| Success
        BuildCheck -->|Fail| RollbackBuild
    end

    subgraph "Rollback"
        RollbackYAML[Detect: YAML error]
        RollbackBuild[Detect: Build error]

        RollbackYAML --> Restore1[Restore mkdocs.yml<br/>from backup]
        RollbackBuild --> Restore2[Restore mkdocs.yml<br/>from backup]

        Restore1 --> ShowError1[Show error:<br/>Invalid YAML]
        Restore2 --> ShowError2[Show error:<br/>Build failed]
    end

    Success([Success!<br/>Files updated]) --> Keep{User commits?}

    Keep -->|Yes| DeleteBackups[Keep backups<br/>for safety]
    Keep -->|No| ManualRollback{User wants<br/>rollback?}

    ManualRollback -->|Yes| RestoreManual[Restore from<br/>backups manually]
    ManualRollback -->|No| KeepBoth[Keep both<br/>files & backups]

    DeleteBackups --> End([Done])
    ShowError1 --> End
    ShowError2 --> End
    RestoreManual --> End
    KeepBoth --> End

    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style End fill:#d4edda
    style RollbackYAML fill:#f8d7da
    style RollbackBuild fill:#f8d7da
    style ShowError1 fill:#f8d7da
    style ShowError2 fill:#f8d7da
```

---

## Time Comparison: Manual vs. Automatic

```mermaid
gantt
    title Documentation Update Time Comparison
    dateFormat X
    axisFormat %s

    section Manual Process
    Read git log           :0, 180s
    Copy commit messages   :180s, 120s
    Format CHANGELOG       :300s, 180s
    Find new docs          :480s, 90s
    Update mkdocs.yml      :570s, 120s
    Update .STATUS         :690s, 90s
    Review & commit        :780s, 120s

    section Automatic Process
    Run /workflow:done     :0, 5s
    Press Enter (3 times)  :5s, 10s
    Review diff            :15s, 15s

    section Time Saved
    15 minutes saved!      :30s, 870s
```

---

## Integration with /workflow:done

```mermaid
sequenceDiagram
    participant U as User
    participant WF as /workflow:done
    participant D as Phase 1: Detect
    participant A as Phase 2: Auto-Update
    participant V as Validation
    participant G as Git

    U->>WF: Run command
    WF->>WF: Step 1: Gather git activity
    WF->>D: Step 1.5: Detect issues

    D->>D: Check CHANGELOG
    D->>D: Check mkdocs.yml
    D->>D: Check .STATUS
    D-->>WF: Found 3 commits, 2 orphaned docs

    WF->>A: Step 1.6: Run auto-updaters

    A->>A: Backup files
    A->>A: Update CHANGELOG
    A->>A: Update mkdocs.yml
    A->>U: Update .STATUS? [Y/n]
    U-->>A: Y
    A->>A: Update .STATUS

    A->>V: Validate changes
    V->>V: Test mkdocs build --strict
    V-->>A: ✓ Build passes

    A->>U: Show diff
    A->>U: Commit changes? [Y/n]
    U-->>A: Y

    A->>G: git add CHANGELOG.md mkdocs.yml .STATUS
    A->>G: git commit -m "docs: auto-update documentation"
    G-->>A: ✓ Committed

    A-->>WF: ✓ Phase 2 complete
    WF->>WF: Step 2: Session summary
    WF->>WF: Step 3: Final cleanup
    WF-->>U: ✓ Done!
```

---

## Decision Tree: Which Mode to Use?

```mermaid
flowchart TD
    Start{What's your<br/>use case?}

    Start -->|Regular dev session| Interactive[Use Interactive Mode<br/>Default behavior]
    Start -->|CI/CD pipeline| Auto[Use Auto Mode<br/>--auto flag]
    Start -->|Want to preview| Preview[Use Preview Mode<br/>--dry-run flag]
    Start -->|Major release| Manual[Manual + Review]

    Interactive --> Q1{Do you trust<br/>the system?}
    Q1 -->|Yes| Fast[Just press Enter<br/>~10 seconds]
    Q1 -->|No| Review1[Review each change<br/>~30 seconds]

    Auto --> Q2{Safe for<br/>automation?}
    Q2 -->|Yes| Safe[CHANGELOG + mkdocs<br/>auto-applied]
    Q2 -->|No| Interactive

    Preview --> Q3{What do you<br/>want to check?}
    Q3 -->|What would change| Show[Shows preview<br/>No changes applied]
    Q3 -->|Why not updating| Debug[Debug detection<br/>logic]

    Manual --> Q4{Why manual?}
    Q4 -->|Breaking changes| Detail[Write detailed<br/>migration guide]
    Q4 -->|Security fix| Specific[Specific wording<br/>for advisory]
    Q4 -->|Marketing| Polish[Polish for<br/>public release]

    Fast --> Done([Done!])
    Review1 --> Done
    Safe --> Done
    Show --> Done
    Debug --> Done
    Detail --> Done
    Specific --> Done
    Polish --> Done

    style Start fill:#e1f5ff
    style Done fill:#d4edda
    style Interactive fill:#fff4e6
    style Auto fill:#ffe6f0
    style Preview fill:#e8f5e9
    style Manual fill:#fff3e0
```

---

## Key Concepts Summary

```mermaid
mindmap
  root((Auto-Update<br/>System))
    3 Updaters
      CHANGELOG
        Parses commits
        Groups by type
        Creates links
      mkdocs.yml
        Finds orphaned docs
        Infers sections
        Extracts titles
      .STATUS
        Generates summary
        Updates fields
        Prepends entries
    3 Modes
      Interactive
        User confirms .STATUS
        Shows diffs
        10-30 seconds
      Auto
        No prompts
        CI/CD ready
        5-10 seconds
      Preview
        No changes
        Dry run
        Debug mode
    Safety Features
      Backups
        Timestamped
        Auto-created
        Easy rollback
      Validation
        YAML syntax
        mkdocs build
        Auto-rollback
      Two-tier
        Safe: auto-apply
        Interactive: confirm
    Integration
      /workflow:done
        Step 1.6
        Automatic
        Seamless
      Manual
        Individual scripts
        More control
        Focused updates
```

---

## Usage Examples by Scenario

```mermaid
flowchart LR
    subgraph "Scenario 1: Daily Development"
        S1[Code all day] --> S1C[Make 5 commits]
        S1C --> S1W[Run /workflow:done]
        S1W --> S1P[Press Enter 3x]
        S1P --> S1D[Done! 30 sec]
    end

    subgraph "Scenario 2: Major Release"
        S2[Ready for v2.0] --> S2A[Run auto-updater]
        S2A --> S2R[Review entries]
        S2R --> S2E[Manually edit CHANGELOG]
        S2E --> S2D[Add migration guide]
        S2D --> S2C[Commit]
    end

    subgraph "Scenario 3: CI/CD Pipeline"
        S3[Push to main] --> S3T[CI triggers]
        S3T --> S3B[Build succeeds]
        S3B --> S3U[Run updater --auto]
        S3U --> S3P[Create PR]
        S3P --> S3M[Merge PR]
    end

    subgraph "Scenario 4: Debug Why Not Updating"
        S4[Why no update?] --> S4D[Run --dry-run]
        S4D --> S4C{What does<br/>it show?}
        S4C --> S4N[No new commits]
        S4C --> S4F[Files excluded]
        S4C --> S4A[Already updated]
    end

    style S1D fill:#d4edda
    style S2C fill:#d4edda
    style S3M fill:#d4edda
    style S4N fill:#fff4e6
    style S4F fill:#fff4e6
    style S4A fill:#fff4e6
```

---

## Conclusion

These diagrams illustrate the complete workflow of the Documentation Auto-Update system:

1. **High-level flow** - From coding to committed documentation
2. **Detailed update** - Each phase with decision points
3. **Individual updaters** - How each script works internally
4. **Safety & rollback** - Protection mechanisms
5. **Time comparison** - Visual proof of time savings
6. **Integration** - How it fits into /workflow:done
7. **Decision tree** - Which mode to use when
8. **Mental model** - Key concepts at a glance
9. **Usage scenarios** - Real-world examples

**For more details, see:**
- Full tutorial: `docs/AUTO-UPDATE-TUTORIAL.md`
- Quick reference: `docs/AUTO-UPDATE-REFCARD.md`
- Design docs: `PHASE-2-DESIGN.md`, `PHASE-2-COMPLETE.md`
