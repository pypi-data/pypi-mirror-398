import {expect, test} from '@jupyterlab/galata';
import CONFIG from './config';
import {Page, TestInfo} from '@playwright/test';

/**
 * Enum for different response states that waitForResponse can return
 */
export enum ResponseState {
    DIFF = 'DIFF',
    WAITING_FOR_USER = 'WAITING_FOR_USER',
    FINISHED = 'FINISHED'
}

/**
 * Don't load JupyterLab webpage before running the tests.
 * This is required to ensure we capture all log messages.
 */
test.use({autoGoto: false});

/**
 * Static screenshot function to capture test states
 */
export async function captureScreenshot(
    page: Page,
    category: string,
    action: string,
    state: string,
    testName?: string,
    testInfo?: any
): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${category}_${action}_${state}_${timestamp}.png`;

    // Create test-specific directory if testName is provided
    let screenshotPath: string;
    if (testName) {
        // Sanitize test name for directory creation
        const sanitizedTestName = testName.toLowerCase().replace(/[^a-z0-9]/g, '_');
        screenshotPath = `${CONFIG.SCREENSHOT_DIR}/${sanitizedTestName}/${filename}`;
    } else {
        screenshotPath = `${CONFIG.SCREENSHOT_DIR}/${filename}`;
    }

    // Playwright will automatically create directories as needed
    await page.screenshot({
        path: screenshotPath,
        fullPage: true
    });
    if (testInfo) {
        await (testInfo as TestInfo).attach(filename, {
            path: screenshotPath,
            contentType: 'image/png'
        });
    }
}

/**
 * API Configuration utility
 */
export class APIConfigurator {
    static async setupJWTToken(
        page: any,
        jwtToken: string,
        modelUrl: string,
        modelId: string
    ): Promise<void> {
        if (!jwtToken) {
            throw new Error('SAGE_JWT_TOKEN not provided in environment variables');
        }

        console.log('🔧 Setting up API configuration...');

        // Wait for JupyterLab to be ready
        await page.waitForSelector('#jp-main-dock-panel');

        // Open command palette using Ctrl+Shift+C
        try {
            console.log('🔧 Opening command palette...');
            await page.keyboard.press('Control+Shift+C');

            // Wait for command palette to appear
            await page.waitForSelector('#modal-command-palette', {timeout: 5000});

            // Find the search input and enter "activate test mode"
            const searchInput = page.locator('.lm-CommandPalette-input');
            await searchInput.fill('activate test mode');

            console.log('🔧 Searching for "activate test mode" command...');

            // Wait for the command to appear in the results
            await page.waitForSelector('.lm-CommandPalette-content', {timeout: 5000});


            // Look for the "Activate Test Mode (Set JWT Token)" command and click it
            const testModeCommand = page.locator('[data-command="signalpilot-ai-internal:activate-test-mode"]');
            await testModeCommand.click();

            console.log('🔧 Test mode activated via command palette');

            // Wait for JWT token input dialog to appear
            console.log('🔧 Waiting for JWT token input dialog...');
            await page.waitForSelector('.sage-ai-dialog-input[placeholder*="JWT token"]', {timeout: 5000});

            // Fill the JWT token into the password input field
            const jwtTokenInput = page.locator('input[type="password"].sage-ai-dialog-input[placeholder*="JWT token"]');
            await jwtTokenInput.fill(jwtToken);
            console.log('🔧 JWT token entered into input field');

            // Click the "Set Token" button
            const setTokenButton = page.locator('button.sage-ai-dialog-submit-button');
            await setTokenButton.click();
            console.log('🔧 "Set Token" button clicked');

            // Click the "OK" button
            await page.waitForSelector('button.sage-ai-dialog-submit-button:has-text("OK")', {timeout: 5000});
            const okButton = page.locator('button.sage-ai-dialog-submit-button:has-text("OK")');
            await okButton.click();
            console.log('🔧 "OK" button clicked');
            await page.waitForTimeout(1000);
            // Wait a bit for DOM to settle
            console.log('🔧 Modal cleanup completed');
        } catch (error) {
            console.error('⚠️ Could not access test mode via command palette, cancelling tests...');
            throw new Error(
                'Command palette or test mode command not found. Ensure the Sage AI extension is installed and enabled.'
            );
        }
    }
}

/**
 * Notebook interaction utility
 */
export class NotebookManager {
    static async createNewNotebook(page: any): Promise<void> {
        console.log('📓 Creating new notebook...');
        //<button type="button" class="sage-ai-jwt-auth-dismiss-btn btn btn-outline-secondary">Continue without login</button>


        // Click on the Python 3 (ipykernel) launcher card
        const launcherCardSelector =
            '.jp-LauncherCard[title="Python 3 (ipykernel)"][role="button"]';

        try {
            // Wait for the launcher card to be available
            await page.waitForSelector(launcherCardSelector, {timeout: 10000});

            // Click on the Python 3 (ipykernel) launcher card
            await page.click(launcherCardSelector);

            console.log('✅ New Python notebook created');

            // Wait for the notebook to load
            await page.waitForTimeout(2000);

            // Press Ctrl+Shift+F at the end
            await page.keyboard.press('Control+Shift+F');
            console.log('✅ Pressed Ctrl+Shift+F');
        } catch (error) {
            console.error('⚠️ Could not create new notebook:', error);
            throw new Error(
                'Failed to create new notebook. Ensure JupyterLab launcher is available.'
            );
        }
    }
}

/**
 * Chat interaction utility
 */
export class ChatInteractor {
    static async waitForChatReady(page: any): Promise<void> {
        // Wait for the sage AI chat container to be present
        const chatContainerSelector = '[data-id="sage-ai-chat-container"]';
        await page.waitForSelector(chatContainerSelector, {
            timeout: 10000
        });
        //
        // await page.click(chatContainerSelector);

        await page.waitForTimeout(1000);

        // Wait for the chat input to be loaded and visible
        const chatContainer = page.locator(chatContainerSelector);
        const chatWidget = chatContainer.locator(
            '#sage-ai-chat.lm-Widget.sage-ai-chatbox'
        );
        const chatInput = chatWidget.locator('.sage-ai-rich-chat-input');
        await page.waitForTimeout(1000);
        console.log('✅ Chat is ready for interaction');
    }

    static async sendMessage(page: any, message: string): Promise<void> {
        const chatContainer = page.locator('#sage-ai-chat-container');
        const chatWidget = chatContainer.locator('.sage-ai-chatbox');
        const chatInput = chatWidget.locator('.sage-ai-rich-chat-input');
        const sendButton = chatWidget.locator('.sage-ai-send-button');

        // Clear and enter message
        await chatInput.click();
        await chatInput.clear();
        await chatInput.fill(message);

        // Send message
        await expect(sendButton).toBeVisible();
        await sendButton.click();
    }

    static async waitForDiffState(
        page: any,
        timeout: number = CONFIG.TEST_TIMEOUT
    ): Promise<boolean> {
        const diffSelector = '.cm-changedLine';
        try {
            // Wait for the diff state to appear in the chat
            await page.waitForSelector(diffSelector, {
                timeout: timeout,
                state: 'visible'
            });
            return true; // Diff state detected
        } catch {
            return false; // Diff state not found
        }
    }

    static async waitForResponse(
        page: any,
        timeout: number = CONFIG.TEST_TIMEOUT
    ): Promise<ResponseState> {
        // Wait for a response to appear in the chat
        await page.waitForSelector('.sage-ai-message:not(.sage-ai-user-message)', {
            timeout: timeout,
            state: 'visible'
        });

        // Use Promise.race to check both selectors simultaneously
        try {
            const result = await Promise.race([
                // Check for diff state (working fine)
                page
                    .waitForSelector('.sage-ai-llm-state-display.sage-ai-diff-state', {
                        timeout: 60000,
                        state: 'visible'
                    })
                    .then(() => ResponseState.DIFF),

                // Check for waiting for user state (Sage will continue working after you reply)
                page
                    .waitForSelector('.sage-ai-waiting-for-user', {
                        timeout: 60000,
                        state: 'visible'
                    })
                    .then(() => ResponseState.WAITING_FOR_USER),

                // Timeout fallback - if neither appears within timeout, assume finished
                new Promise<ResponseState>(resolve => {
                    setTimeout(() => resolve(ResponseState.FINISHED), 60000);
                })
            ]);

            return result;
        } catch (error) {
            // If all promises reject, assume finished state
            console.warn(
                'waitForResponse: No expected state found, assuming finished',
                error
            );
            return ResponseState.FINISHED;
        }
    }

    static async waitForGeneratingState(page: any): Promise<boolean> {
        try {
            // Look for generating indicators
            const generatingSelectors = [
                '.sage-ai-generating',
                '.sage-ai-loading',
                '[data-testid="generating"]',
                '.spinning',
                '.loading-dots'
            ];

            for (const selector of generatingSelectors) {
                if ((await page.locator(selector).count()) > 0) {
                    return true;
                }
            }

            // Alternative: Check if send button is disabled (indicating processing)
            const sendButton = page.locator('.sage-ai-send-button');
            const isDisabled = await sendButton.getAttribute('disabled');
            return isDisabled !== null;
        } catch {
            return false;
        }
    }

    static async waitForDiffApprovalState(page: any): Promise<boolean> {
        try {
            // Look for diff approval UI elements
            const diffSelectors = [
                '.sage-ai-diff',
                '.sage-ai-code-diff',
                '[data-testid="diff-approval"]',
                'button:has-text("Accept")',
                'button:has-text("Reject")',
                '.diff-container'
            ];

            for (const selector of diffSelectors) {
                if ((await page.locator(selector).count()) > 0) {
                    return true;
                }
            }
            return false;
        } catch {
            return false;
        }
    }

    static async setupMultiDiffState(
        page: any,
        testName: string,
        testInfo: any
    ): Promise<any> {
        console.log(`🧪 Setting up Multi-Diff state for ${testName}`);

        // Send multi-file diff prompt
        await ChatInteractor.sendMessage(page, TEST_PROMPTS.MULTI_DIFF[0]);
        await captureScreenshot(
            page,
            'generation',
            'generating',
            'multi_diff_sent',
            testName,
            testInfo
        );

        // Capture generating state
        if (await ChatInteractor.waitForGeneratingState(page)) {
            await captureScreenshot(
                page,
                'generation',
                'generating',
                'multi_file_progress',
                testName,
                testInfo
            );
        }

        // Wait for response
        await ChatInteractor.waitForResponse(page);

        // Check for multi-diff approval state and return diff items
        if (await ChatInteractor.waitForDiffApprovalState(page)) {
            await captureScreenshot(
                page,
                'diff_approval',
                'multi_approval',
                'multiple_files',
                testName
            );

            // Verify we have exactly 3 diff items
            const diffList = page.locator('.sage-ai-diff-list');
            await expect(diffList).toBeVisible();
            const diffItems = diffList.locator('> *'); // Direct children of diff list
            await expect(diffItems).toHaveCount(3);
            console.log('✅ Confirmed 3 diff items in the list');

            await captureScreenshot(
                page,
                'diff_approval',
                'verified',
                'three_diffs_confirmed',
                testName
            );

            return diffItems;
        }

        throw new Error('Failed to reach diff approval state');
    }

    static async handleRunAllButtons(
        page: any,
        testName: string,
        loopCounter: number,
        testInfo?: any
    ): Promise<void> {
        console.log(`🔄 Handling Run All buttons in loop ${loopCounter}`);

        // Look for the first Run All button (sage-ai-diff-btn sage-ai-diff-approve-all)
        const runAllButton1 = page.locator(
            'button.sage-ai-diff-btn.sage-ai-diff-approve-all[title="Run all changes"]'
        );

        // Look for the second Run All button (with icon)
        const runAllButton2 = page.locator(
            'button.sage-ai-diff-navigation-action-button.sage-ai-diff-navigation-accept-run-button'
        );

        // Look for Approve All buttons as fallback when Run All is not present
        const approveAllButton = page.locator(
            'button.sage-ai-diff-btn.sage-ai-diff-approve-all[title="Approve false changes"]'
        );

        await captureScreenshot(
            page,
            'diff_handling',
            'before_run_all',
            `loop_${loopCounter}_before_run_all`,
            testName,
            testInfo
        );

        let buttonClicked = false;

        // Try clicking the first Run All button
        if ((await runAllButton1.count()) > 0) {
            console.log(
                '🎯 Clicking first Run All button (sage-ai-diff-approve-all)'
            );
            await runAllButton1.click();
            buttonClicked = true;
            await captureScreenshot(
                page,
                'diff_handling',
                'run_all_1_clicked',
                `loop_${loopCounter}_run_all_1_clicked`,
                testName,
                testInfo
            );
        }

        // Wait a moment for UI to update
        await page.waitForTimeout(1000);

        // Try clicking the second Run All button
        if ((await runAllButton2.count()) > 0) {
            console.log('🎯 Clicking second Run All button (navigation accept run)');
            await runAllButton2.click();
            buttonClicked = true;
            await captureScreenshot(
                page,
                'diff_handling',
                'run_all_2_clicked',
                `loop_${loopCounter}_run_all_2_clicked`,
                testName,
                testInfo
            );
        }

        // If no Run All buttons were found, try Approve All button
        if (!buttonClicked && (await approveAllButton.count()) > 0) {
            console.log('🎯 No Run All buttons found, clicking Approve All button');
            await approveAllButton.click();
            buttonClicked = true;
            await captureScreenshot(
                page,
                'diff_handling',
                'approve_all_clicked',
                `loop_${loopCounter}_approve_all_clicked`,
                testName,
                testInfo
            );
        }

        // Wait for the execution to complete
        await page.waitForTimeout(2000);

        await captureScreenshot(
            page,
            'diff_handling',
            'after_run_all',
            `loop_${loopCounter}_after_run_all`,
            testName,
            testInfo
        );

        if (buttonClicked) {
            console.log('✅ Run All/Approve All buttons handling completed');
        } else {
            console.log('⚠️ No Run All or Approve All buttons found to click');
        }
    }
}

/**
 * Prompts for triggering different states - now imported from config.json
 */
export const TEST_PROMPTS = CONFIG.TEST_PROMPTS;

test.describe('Sage LLM State Testing', () => {
    test.beforeAll(async () => {
        // Validate configuration before starting tests
        if (CONFIG.SAGE_JWT_TOKEN === 'your-api-key-here' || !CONFIG.SAGE_JWT_TOKEN) {
            throw new Error(
                '❌ API Key not configured! Please set CONFIG.SAGE_API_KEY in the test file before running tests.'
            );
        }
        console.log('✅ Configuration validated');
    });

    test.beforeEach(async ({page, baseURL}) => {

        const closeWelcomeModal = async () => {
            const welcomeSelector = 'button.sage-ai-jwt-auth-dismiss-btn.btn.btn-outline-secondary';
            await page.waitForSelector(welcomeSelector, {timeout: 30000});
            await page.click(welcomeSelector);
            await page.waitForTimeout(500);
        }

        // Navigate to JupyterLab
        try {
            await Promise.all([
                closeWelcomeModal(),
                page.goto(`${baseURL}`)
            ])
        } catch (error) {
            console.log("ignore this error");
            throw error;
        }


        // Create a new notebook before each test
        await NotebookManager.createNewNotebook(page);

        // Setup API configuration
        await APIConfigurator.setupJWTToken(
            page,
            CONFIG.SAGE_JWT_TOKEN,
            CONFIG.CLAUDE_MODEL_URL,
            CONFIG.CLAUDE_MODEL_ID
        );

        // Additional cleanup and stabilization
        await page.evaluate(() => {
            // Final cleanup pass
            const allModals = document.querySelectorAll('div[role="dialog"], .modal, .fade, .modal-backdrop');
            allModals.forEach(modal => modal.remove());

            // Reset body state
            document.body.className = document.body.className.replace(/modal-open|fade/g, '');
            document.body.style.cssText = '';
        });

        // Force page to be interactive
        await page.keyboard.press('Escape'); // Clear any lingering UI states
        await page.waitForTimeout(500);

        // Wait for chat to be ready
        await ChatInteractor.waitForChatReady(page);
    });

    test('Chatbox Opens and is Ready', async ({page}, testInfo) => {
        console.log('🧪 Testing that Chatbox Opens');

        // Capture empty interface
        await captureScreenshot(
            page,
            'idle',
            'none',
            'empty_interface',
            'Chatbox Opens and is Ready',
            testInfo
        );

        // Verify chat input is ready but empty
        const chatInput = page.locator('.sage-ai-rich-chat-input');
        await expect(chatInput).toBeVisible();
        await expect(chatInput).toBeEmpty();
    });

    test('Single File Diff States', async ({page}, testInfo) => {
        console.log('🧪 Testing Single File Diff States');

        // Send diff-generating prompt
        await ChatInteractor.sendMessage(page, TEST_PROMPTS.SINGLE_DIFF[0]);
        await captureScreenshot(
            page,
            'generation',
            'generating',
            'single_diff_sent',
            'Single File Diff States',
            testInfo
        );

        // Capture generating state
        if (await ChatInteractor.waitForGeneratingState(page)) {
            await captureScreenshot(
                page,
                'generation',
                'generating',
                'in_progress',
                'Single File Diff States',
                testInfo
            );
        }

        // Wait for response and potential diff
        const responseState = await ChatInteractor.waitForResponse(page);

        const waitForDiff = await ChatInteractor.waitForDiffState(page);

        // Handle different response states
        switch (responseState) {
            case ResponseState.DIFF:
                await captureScreenshot(
                    page,
                    'generation',
                    'complete',
                    'diff_state',
                    'Single File Diff States',
                    testInfo
                );
                break;
            case ResponseState.WAITING_FOR_USER:
                await captureScreenshot(
                    page,
                    'generation',
                    'complete',
                    'waiting_for_user',
                    'Single File Diff States',
                    testInfo
                );
                break;
            case ResponseState.FINISHED:
                await captureScreenshot(
                    page,
                    'generation',
                    'complete',
                    'finished',
                    'Single File Diff States',
                    testInfo
                );
                break;
        }

        // Check for diff approval state
        if (await ChatInteractor.waitForDiffApprovalState(page)) {
            await captureScreenshot(
                page,
                'diff_approval',
                'single_approval',
                'awaiting_decision',
                'Single File Diff States',
                testInfo
            );

            // Test accepting diff
            const acceptButton = page.locator('button:has-text("Accept")');
            if ((await acceptButton.count()) > 0) {
                await acceptButton.click();
                await captureScreenshot(
                    page,
                    'diff_approval',
                    'single_accepted',
                    'after_accept',
                    'Single File Diff States',
                    testInfo
                );
            }
        }
    });

    test('sp500_test', async ({ page }, testInfo) => {
      testInfo.setTimeout(600_000);
      console.log(
        '🧪 Testing S&P 500 Analysis with wait_for_user_reply handling'
      );

      page.video();

      const testName = 'sp500_test';
      let waitForUserReplyCounter = 0;
      let loopCounter = 0;
      const maxLoops = 15; // Safety limit to prevent infinite loops

      // Send the SP_ANALYSIS prompt
      await ChatInteractor.sendMessage(page, TEST_PROMPTS.SP_ANALYSIS[0]);
      await captureScreenshot(
        page,
        'generation',
        'generating',
        'sp500_analysis_sent',
        testName,
        testInfo
      );

      // Capture initial generating state
      if (await ChatInteractor.waitForGeneratingState(page)) {
        await captureScreenshot(
          page,
          'generation',
          'generating',
          'sp500_initial_progress',
          testName,
          testInfo
        );
      }

      // Main loop to handle responses and user interactions
      while (loopCounter < maxLoops) {
        loopCounter++;
        console.log(`🔄 Loop iteration ${loopCounter}`);

        // Wait for response
        const responseState = await ChatInteractor.waitForResponse(page);
        console.log(`🔍 Response state detected: ${responseState}`);

        await captureScreenshot(
          page,
          'generation',
          'response',
          `loop_${loopCounter}_state_${responseState}`,
          testName,
          testInfo
        );

        // Handle different response states
        switch (responseState) {
          case ResponseState.DIFF:
            console.log(`📊 Diff state detected in loop ${loopCounter}`);
            await captureScreenshot(
              page,
              'diff_approval',
              'diff_detected',
              `loop_${loopCounter}_diff_state`,
              testName,
              testInfo
            );

            // Look for and click Run All buttons
            await ChatInteractor.handleRunAllButtons(
              page,
              testName,
              loopCounter,
              testInfo
            );
            break;

          case ResponseState.WAITING_FOR_USER:
            waitForUserReplyCounter++;
            console.log(
              `⏳ Wait for user reply detected (count: ${waitForUserReplyCounter}) in loop ${loopCounter}`
            );

            await captureScreenshot(
              page,
              'user_interaction',
              'waiting_for_user',
              `loop_${loopCounter}_wait_${waitForUserReplyCounter}`,
              testName,
              testInfo
            );

            if (waitForUserReplyCounter === 1) {
              // First wait_for_user_reply - respond with "Continue"
              console.log(
                '💬 Responding with "Continue" to first wait_for_user_reply'
              );
              await ChatInteractor.sendMessage(page, 'Continue');

              await captureScreenshot(
                page,
                'user_interaction',
                'continue_sent',
                `loop_${loopCounter}_continue_sent`,
                testName,
                testInfo
              );
            } else {
              // Second or subsequent wait_for_user_reply - exit the loop
              console.log(
                `🏁 Second wait_for_user_reply detected, ending test at loop ${loopCounter}`
              );
              await captureScreenshot(
                page,
                'completion',
                'final_wait',
                `loop_${loopCounter}_final_wait`,
                testName,
                testInfo
              );
              console.log('✅ Test completed successfully, saving video');
              await page.close();
              await page
                .video()
                .saveAs(CONFIG.SCREENSHOT_DIR + `/${testName}_final.mp4`);
              await testInfo.attach('Final Video', {
                path: CONFIG.SCREENSHOT_DIR + `/${testName}_final.mp4`,
                contentType: 'video/mp4'
              });
              console.log('🎥 Video saved successfully');
              return; // Exit the test
            }
            break;

          case ResponseState.FINISHED:
            console.log(`✅ Finished state detected in loop ${loopCounter}`);
            await captureScreenshot(
              page,
              'completion',
              'finished',
              `loop_${loopCounter}_finished`,
              testName,
              testInfo
            );
            return; // Exit the test

          default:
            console.log(
              `❓ Unknown response state in loop ${loopCounter}: ${responseState}`
            );
            await captureScreenshot(
              page,
              'unknown',
              'unknown_state',
              `loop_${loopCounter}_unknown`,
              testName,
              testInfo
            );
        }

        // Short wait before next iteration
        await page.waitForTimeout(1000);
      }

      console.log(`⚠️ Test reached maximum loops (${maxLoops}), ending test`);
      await captureScreenshot(
        page,
        'completion',
        'max_loops_reached',
        `final_max_loops`,
        testName,
        testInfo
      );
      console.log('✅ Test completed, saving final video');
      await page.close();
      await page.video().saveAs(CONFIG.SCREENSHOT_DIR + `/${testName}_final.mp4`);
      await testInfo.attach('Final Video', {
        path: CONFIG.SCREENSHOT_DIR + `/${testName}_final.mp4`,
        contentType: 'video/mp4'
      });
      console.log('🎥 Final video saved successfully');
    });
});
