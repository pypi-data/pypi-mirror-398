# Browser Examples

This directory contains examples demonstrating various capabilities of the AgentBay browser automation system.

## Screenshot Examples

### [browser_screenshot.py](../browser/browser_screenshot.py) - Browser Screenshot Demo

Demonstrates how to capture screenshots using both the browser agent and direct Playwright integration methods:

- Creating a browser session with AgentBay
- Using Playwright to connect to the browser instance
- Taking screenshots using the browser agent (returns base64 data)
- Taking screenshots using direct Playwright integration (returns bytes data)
- Saving screenshots to local files
- Customizing screenshot options (full page, image format, quality)

**Key Features:**
1. **Browser Agent Screenshots** - Uses `session.browser.agent.screenshot_async()` which returns base64 encoded data
2. **Direct Playwright Screenshots** - Uses `session.browser.screenshot(page)` which returns raw bytes data
3. **Multiple Formats** - Supports both PNG and JPEG formats with customizable quality
4. **Full Page Capture** - Ability to capture entire web pages including content below the fold
5. **Custom Options** - Configurable timeout, viewport settings, and other advanced options

**Usage:**
```bash
export AGENTBAY_API_KEY=your_api_key_here
python browser_screenshot.py
```

This will generate several screenshot files in the current directory:
- `temp_agent_screenshot.png` - Screenshot taken with browser agent
- `temp_agent_full_page_screenshot.png` - Full page screenshot taken with browser agent
- `temp_browser_screenshot.png` - Screenshot taken with direct Playwright integration
- `temp_browser_full_page_screenshot.jpg` - Full page screenshot in JPEG format
- `temp_browser_custom_screenshot.png` - Screenshot with custom options

## Other Examples

### [visit_aliyun.py](../browser/visit_aliyun.py) - Basic Browser Usage
Demonstrates basic browser automation capabilities:
- Create browser session
- Use Playwright to connect to browser instance through CDP protocol
- Navigate to websites and interact with page content

### [browser_viewport.py](../browser/browser_viewport.py) - Viewport Configuration
Shows how to configure browser viewport and screen dimensions:
- Custom viewport sizes for different device types
- Screen resolution configuration
- Responsive design testing

### [browser-proxies.py](../browser/browser-proxies.py) - Proxy Configuration
Shows how to configure browser proxies:
- Custom proxy servers
- Authentication with username/password
- Wuying proxy integration

### [browser_type_example.py](../browser/browser_type_example.py) - Browser Type Selection
Demonstrates browser type selection:
- Chrome vs Chromium selection
- Computer use image requirements
- Browser compatibility considerations

### [browser_command_args.py](../browser/browser_command_args.py) - Command Line Arguments
Shows how to customize browser behavior with command-line arguments:
- Feature flags and switches
- Performance optimizations
- Debugging options

### [captcha_tongcheng.py](../browser/captcha_tongcheng.py) - CAPTCHA Handling
Demonstrates CAPTCHA solving capabilities:
- Automated CAPTCHA detection
- Integration with solving services
- Error handling and retry logic

### [game_2048.py](../browser/game_2048.py) - Game Automation
Advanced example of game automation:
- Complex interaction patterns
- State detection and response
- AI-driven decision making

### [shop_inspector.py](../browser/shop_inspector.py) - E-commerce Scraping
Comprehensive e-commerce site inspection:
- Product extraction and normalization
- Screenshot capture for verification
- Data validation and filtering

### [search_agentbay_doc.py](../browser/search_agentbay_doc.py) - Documentation Search
Demonstrates search automation:
- Form filling and submission
- Result parsing and extraction
- Multi-page navigation

### [admin_add_product.py](../browser/admin_add_product.py) - Admin Panel Automation
Complex admin panel workflow automation:
- Authentication and session management
- Multi-step form completion
- File uploads and image processing

### [mini_max.py](../browser/mini_max.py) - AI Platform Integration
Integration with AI platforms:
- Login and authentication workflows
- Content generation and management
- Result validation and processing

### [expense_upload_invoices.py](../browser/expense_upload_invoices.py) - File Upload Automation
File upload and processing automation:
- Document upload workflows
- Form completion and submission
- Status monitoring and verification

### [game_sudoku.py](../browser/game_sudoku.py) - Logic Game Automation
Logic puzzle automation:
- Grid recognition and parsing
- Rule-based solving algorithms
- Interactive gameplay

### [gv_quick_buy_seat.py](../browser/gv_quick_buy_seat.py) - Ticket Booking Automation
High-speed booking automation:
- Time-sensitive operations
- Multi-step checkout processes
- Error handling and recovery

### [alimeeting_availability.py](../browser/alimeeting_availability.py) - Calendar Integration
Calendar and scheduling automation:
- Availability checking
- Time slot selection
- Meeting scheduling workflows

### [sudoku_solver.py](../browser/sudoku_solver.py) - Simple Game Solver
Simple game automation example:
- Basic interaction patterns
- State evaluation
- Move execution

### [search_agentbay_doc_by_agent.py](../browser/search_agentbay_doc_by_agent.py) - Agent-Based Search
Agent-driven search automation:
- Natural language instructions
- Autonomous navigation
- Result extraction

### [browser_context_cookie_persistence.py](../browser/browser_context_cookie_persistence.py) - Cookie Management
Cookie persistence and management:
- Session preservation
- Authentication state management
- Context isolation

### [browser_replay.py](../browser/browser_replay.py) - Browser Replay
Browser session recording and replay:
- Action recording
- Playback automation
- Screenshot capture for verification

### [call_for_user_jd.py](../browser/call_for_user_jd.py) - User Simulation
User behavior simulation:
- Realistic interaction patterns
- Timing variations
- Error handling