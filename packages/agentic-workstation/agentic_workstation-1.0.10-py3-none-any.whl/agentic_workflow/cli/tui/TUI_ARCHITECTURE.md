# Agentic Workflow OS TUI Reference

## Purpose
A deterministic, menu-driven Rich/Questionary TUI that orchestrates project and agent workflows without embedding business logic. All state mutations live in services/handlers; the TUI only renders and routes.

**Status:** Post-refactor v1.0.10 - Single console ownership, handler-only data access, TUI-native feedback/input, theme integration complete, error handling standardized, CLI-TUI consistency achieved.

## Architecture Overview
- **Entry**: `tui/main.py` instantiates `TUIApp` with shared `Console`, `LayoutManager`, `InputHandler`, `Theme`, `FeedbackPresenter`, and `ProgressPresenter` via `TUIContext` dataclass.
- **Controllers** (`cli/tui/controllers/`): Route user intent; never perform business logic directly. Key controllers: `GlobalMenuController`, `ProjectMenuController`, `ProjectWizardController`, `ProjectManagementController`, `WorkflowStatusController`, `AgentOperationsController`, `ArtifactManagementController`, `SystemInfoController`, `ProjectNavigationController`.
- **Views** (`cli/tui/views/`): Pure renderers using Rich components. Examples: `DashboardView`, `ProjectListView`, `ErrorView`.
- **UI Utilities** (`cli/tui/ui/`): Layout, theming, input, feedback, progress. `LayoutManager` standardizes screen composition; `InputHandler` normalizes exits; `Theme` centralizes colors; `FeedbackPresenter` and `ProgressPresenter` use theme maps and route status through `LayoutManager.render_status` to avoid panel stacking.
- **Handlers/Services** (`cli/handlers.py` etc.): All business operations, I/O, and state come from handlers. Controllers only call them and render results.

## Key Architectural Achievements

- **Theme Integration Complete**: All components use `Theme.get_color_map()` for consistent theming
- **Error Handling Standardized**: TUI uses `FeedbackPresenter` for inline errors instead of modal dialogs
- **Input Consistency**: All input operations properly handle `InputResult.EXIT` and cancellation
- **Data Sorting**: Artifact listings are alphabetically sorted for better user experience
- **Clean Separation**: Zero business logic violations; all operations routed through handlers

## Rendering and Layout
- **Clearing policy**: `LayoutManager.render_screen(clear=False)` is opt-in. Avoid unnecessary clears; they create visible blank gaps and scrollback noise. Use `clear=True` only when a screen must replace the prior one (e.g., wizard steps, error modals). Controllers should not call `console.clear()` directly.
- **Header/Body/Footer**: `render_screen` composes a header panel, body content (Rich renderable or string), and optional footer. Do not insert extra blank `print()` calls; keep vertical spacing tight. For custom layouts, render panels directly via views.
- **Status/Footer**: Use `LayoutManager.render_status` for feedback/progress messages to consolidate status output and prevent panel stacking. Presenters (`FeedbackPresenter`, `ProgressPresenter`) route through this method when a layout is provided.
- **Dashboard**: `DashboardView` uses compact `Columns` for info panels and a stacked activity panel. Keep padding minimal `(0,1)` and prefer `expand=True` for tables.
## Branding and Styling
- **Branding Module** (`tui/branding.py`): Simplified branding system for professional ASCII art display with theme integration.
  - `get_agentic_ascii_art_colored()`: Returns themed ASCII art
  - `display_context_header(context=None)`: Unified header display for basic, Global, and Project modes
- **Context-Aware Headers**: Single function handles all header variations with optional context hints below the panel.

## Input and Flow
- **Selections**: `InputHandler.get_selection` auto-adds a Cancel/Exit choice unless one exists. Always check for `InputResult.EXIT` and return to the parent context cleanly.
- **Text/Confirm**: `get_text` and `get_confirmation` also return `InputResult.EXIT` on Ctrl+C. Handle this explicitly to avoid tracebacks.
- **Pauses**: Use `input_handler.wait_for_user()` after showing results to keep the screen readable. Avoid stacking panels; prefer a single render then pause.

## Styling Rules
- **Theme Integration**: All components use `Theme.get_color_map()` method for consistent theming. No direct theme attribute access.
- **Theme Maps**: Components receive theme maps via constructor injection or `Theme.get_color_map()` calls.
- **No Inline Colors**: All colors sourced from theme system; no hardcoded color strings in components.
- **Panels**: Keep `padding` small (typically `(0,1)`), `border_style` from theme, and concise titles. Avoid markup inside titles when possible to prevent width inflation.
- **Tables**: Set widths/ratios and `overflow="fold"` for long text. Use `expand=True` to fill available space without adding whitespace.

## Separation of Concerns
- Controllers should only: collect input, call handlers, and render views. No file I/O, config parsing, or business rules inside controllers/views.
- Views should be pure renderers: consume prepared data; never mutate state or call handlers.
- Handlers/services own all side effects and validation.

## Error and Status Handling
- Use `ErrorView` for modal-style errors; `FeedbackPresenter` for inline status (success/error/info/warning). Prefer a single status panel over multiple stacked prints.
- Catch `AgenticWorkflowError` in `TUIApp.run` and show via `error_view.display_error_modal`.

## Navigation Rules
- **Global context**: `GlobalMenuController.run_menu()` loops until Exit. On create success, exit TUI. On manage/info/list, return to menu.
- **Project context**: `ProjectMenuController.run_menu()` returns `ContextState.GLOBAL` on cancel/exit; callers must switch context accordingly. Never trap the user in project context on cancel.
- **Wizard**: Use explicit `clear=True` per step to keep focus. Confirmations must short-circuit on exit. When launched from TUI, pass shared `console`, `input_handler`, `feedback`, and optionally `layout` to `run_setup_wizard` to avoid new console instantiation.
- **Navigation view (dynamic)**: `ProjectNavigationController` consumes `query_handlers.get_project_inventory(project_root)` to render a table of whatever exists in the root (dirs first with counts, then files). No hardcoded directory names.

## Change Guidelines (must follow before edits)
- `SessionHandlers.handle_init` must use real project root contents when showing the creation summary. The helper `_summarize_root_entries` walks top-level entries (excluding dotfiles), counts items in directories, and passes that list to `display_project_summary`.
- Do not hardcode directory names in creation success UX; rely on the inventory of `result.target_path` so workflows with different scaffolds render correctly.
1. **Preserve clean core**: Do not move business logic into TUI; add new handler methods instead of embedding logic in controllers/views.
2. **Minimize clears**: Default to `clear=False`. Only enable when replacing the full screen. Never chain multiple clears.
3. **Reuse LayoutManager**: Do not hand-roll headers/footers; use `render_screen` or view renderers for consistency. Use `render_status` for status messages to avoid stacking.
4. **Respect InputResult**: Every input call must handle `InputResult.EXIT` without exceptions or loops that ignore the sentinel.
5. **Theme compliance**: Add any new colors/styles to `Theme`; avoid inline styles. Ensure presenters use theme maps.
6. **Compact spacing**: Avoid extra blank `print()` calls. Keep padding small. Prefer columns/grids over wide ratios that create empty vertical space.
7. **Logging/printing**: TUI must not log to stdout directly beyond Rich renders; no `print()` for debugging in committed code.
8. **Data provenance**: Any dynamic data in views (directories, counts, status) must come through handlers (e.g., QueryHandlers inventory, dashboard data). Controllers must not call services directly or inspect the filesystem on their own.
9. **Shared components**: Always inject shared `TUIContext` components (console, layout, input_handler, etc.) into new controllers/views to maintain single ownership.
10. **Testing**: Run `pytest tests/simulation/ -m simulation` for TUI flow regressions when layout or input behavior changes; at minimum, manually sanity-check global/project menus and wizard flows.

## Recent Improvements (v1.0.10)

- **Theme Access Pattern**: Controllers use `self.theme.get_color_map()` while views receive `theme_map` as constructor parameter and store as `self.theme_map`
- **Error Handling Unified**: TUI now uses `FeedbackPresenter` for inline errors instead of modal dialogs, matching CLI behavior
- **Input Consistency**: All input operations properly handle `InputResult.EXIT` and cancellation flows
- **Data Presentation**: Artifact listings are now alphabetically sorted for better user experience
- **Code Cleanup**: Removed unused input utilities and standardized component interfaces

## Quick File Map
- `tui/main.py`: App wiring, context loop, TUIContext dataclass.
- `tui/controllers/`: Menu controllers (global/project/wizard/etc.).
- `tui/views/`: Renderers (dashboard, lists, errors).
- `tui/ui/layout.py`: LayoutManager (headers/body/footers, clearing policy, render_status).
- `tui/ui/input.py`: InputHandler and InputResult.
- `tui/ui/theme.py`: Theme maps.
- `tui/ui/feedback.py`: FeedbackPresenter (routes through layout).
- `tui/ui/progress.py`: ProgressPresenter (routes through layout).
- `cli/ui_utils.py`: ASCII art and misc. helpers.

## Working Checklist for Changes
- [ ] **Theme Compliance**: Controllers use `self.theme.get_color_map()`; views use injected `theme_map` parameter stored as `self.theme_map`
- [ ] **Error Handling**: Use `FeedbackPresenter` for inline errors; `ErrorView` only for modals
- [ ] **Input Handling**: Always check for `InputResult.EXIT` and handle cancellation gracefully
- [ ] **Data Sorting**: Sort any user-visible lists (artifacts, projects, etc.) for consistent UX
- [ ] Identify which layer needs the change (controller/view/handler).
- [ ] Ensure data prep is in handlers; controllers only orchestrate.
- [ ] Choose rendering path: `render_screen` vs. dedicated view.
- [ ] Decide on clear policy (default False; opt-in True only if replacing screen).
- [ ] Handle `InputResult.EXIT` for every prompt.
- [ ] Use theme styles; set padding/ratios consciously.
- [ ] Inject shared TUIContext components into new classes.
- [ ] Add/adjust tests or manual steps for the affected flow.
