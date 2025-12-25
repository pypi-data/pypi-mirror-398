/**
 * GDS Viewer JavaScript functionality
 * This file contains the client-side JavaScript for the GDS viewer
 */

// Global variable to track if we're dealing with a temporary RDB
let tempRdb = false;
// Global variable to track if move functionality is enabled
let moveEnabled = true;
// Global variable to track the theme
let theme = "dark";

/**
 * Initialize the viewer when the page loads
 */
function initializeViewer(
    isTempRdb,
    isMoveEnabled = true,
    viewerTheme = "dark",
) {
    tempRdb = isTempRdb;
    moveEnabled = isMoveEnabled;
    theme = viewerTheme;

    window.onload = () => {
        setTimeout(() => {
            const categoryOptionsEl =
                document.getElementById("rdbCategoryOptions");
            const cellOptionsEl = document.getElementById("rdbCellOptions");
            const rdbItemsEl = document.getElementById("rdbItems");

            if (tempRdb) {
                document.getElementById("rdb-tab").click();

                // Select first category
                for (const option of categoryOptionsEl.options) {
                    categoryOptionsEl.value = option.value;
                }
                const changeEvent = new Event("change");
                console.log("value", categoryOptionsEl.value);
                categoryOptionsEl.dispatchEvent(changeEvent);

                // Select first cell
                for (const option of cellOptionsEl.options) {
                    cellOptionsEl.value = option.value;
                }
                cellOptionsEl.dispatchEvent(changeEvent);

                // Select all items after a delay
                setTimeout(() => {
                    for (const option of rdbItemsEl.options) {
                        option.selected = true;
                    }
                    requestItemDrawings();
                }, 200);
            }

            // Disable move tool if moveEnabled is false
            if (!moveEnabled) {
                const moveToolButton = document.getElementById("tool-move");
                if (moveToolButton) {
                    moveToolButton.disabled = true;
                    moveToolButton.title =
                        "Moving instances is disabled for cells from python source";
                    // Add visual styling to indicate disabled state
                    moveToolButton.style.opacity = "0.5";
                    moveToolButton.style.cursor = "not-allowed";
                }
            }

            // Click darkmode button if theme is light
            if (theme === "light") {
                const darkmodeButton = document.getElementById("darkmode-btn");
                if (darkmodeButton) {
                    darkmodeButton.click();
                }
            }
        }, 500);
    };
}

/**
 * Set up message listener for communication with the parent window
 */
function setupMessageListener() {
    window.addEventListener("message", (event) => {
        let message;
        if (typeof event.data === "string") {
            let content = event.data.trim();
            if (
                content.startsWith("<report-database>") ||
                content.startsWith("<?xml")
            ) {
                console.log(content);
                sendLyrdb(content);
                return;
            }
            message = JSON.parse(content);
        } else {
            message = event.data;
        }

        // Ignore messages intended for doweb (waypoint editor, etc.)
        if (message.command || !message) {
            return;
        }

        const categoryOptionsEl = document.getElementById("rdbCategoryOptions");
        const cellOptionsEl = document.getElementById("rdbCellOptions");
        const rdbItemsEl = document.getElementById("rdbItems");

        // Handle refresh request - equivalent to a browser refresh
        if (message.refresh) {
            window.location.reload();
            return;
        }

        // Handle reload request - just reloads the GDS without refreshing the page
        if (message.reload) {
            const previousMode = currentMode;
            document.getElementById("reload").click();

            const row = document.getElementById("mode-row");
            if (row) {
                for (const child of row.children) {
                    if (child.checked) {
                        child.click();
                        break;
                    }
                }
            }

            if (typeof selectTool !== "undefined" && selectTool) {
                selectTool(previousMode);
            }
            return;
        }

        // Handle RDB item selection
        const category = message.category;
        const cell = message.cell;
        const itemIdxs = message.itemIdxs;

        console.log(`CATEGORY=${category}`);
        console.log(`CELL=${cell}`);
        console.log(`itemIdxs=${itemIdxs}`);

        // Switch to RDB tab
        document.getElementById("rdb-tab").click();

        // Build category and cell option maps
        const categoryOptions = Array.from(categoryOptionsEl.children)
            .map((c) => [c.innerHTML, c.value])
            .reduce((acc, [key, value]) => {
                acc[key] = value;
                return acc;
            }, {});

        const cellOptions = Array.from(cellOptionsEl.children)
            .map((c) => [c.innerHTML, c.value])
            .reduce((acc, [key, value]) => {
                acc[key] = value;
                return acc;
            }, {});

        console.log(categoryOptions);
        console.log(cellOptions);

        // Get indices and set values
        const cellIndex = cellOptions[cell];
        const categoryIndex = categoryOptions[category];
        console.log(`cellIndex: ${cellIndex}`);
        console.log(`categoryIndex: ${categoryIndex}`);

        categoryOptionsEl.value = categoryIndex;
        cellOptionsEl.value = cellIndex;

        // Dispatch change events
        const changeEvent = new Event("change");
        categoryOptionsEl.dispatchEvent(changeEvent);
        cellOptionsEl.dispatchEvent(changeEvent);

        // Select specified items after a delay
        setTimeout(() => {
            for (const itemIndex of itemIdxs) {
                const idx = `${itemIndex}`;
                const option = rdbItemsEl.options[idx];
                if (option) {
                    option.selected = true;
                }
                requestItemDrawings();
            }
        }, 200);
    });
}

// Export functions for use in the HTML
window.gdsViewer = {
    initializeViewer,
    setupMessageListener,
};
