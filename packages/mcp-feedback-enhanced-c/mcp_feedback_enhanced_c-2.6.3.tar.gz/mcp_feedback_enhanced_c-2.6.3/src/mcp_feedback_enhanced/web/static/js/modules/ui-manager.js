/**
 * MCP Feedback Enhanced - UI 管理模組
 * =================================
 * 
 * 處理 UI 狀態更新、指示器管理和頁籤切換
 */

(function() {
    'use strict';

    // 確保命名空間和依賴存在
    window.MCPFeedback = window.MCPFeedback || {};
    const Utils = window.MCPFeedback.Utils;

    /**
     * UI 管理器建構函數
     */
    function UIManager(options) {
        options = options || {};
        
        // 當前狀態
        this.currentTab = options.currentTab || 'combined';
        this.feedbackState = Utils.CONSTANTS.FEEDBACK_WAITING;
        this.layoutMode = options.layoutMode || 'combined-vertical';
        this.lastSubmissionTime = null;
        
        // UI 元素
        this.connectionIndicator = null;
        this.connectionText = null;
        this.tabButtons = null;
        this.tabContents = null;
        this.submitBtn = null;
        this.feedbackText = null;
        
        // 回調函數
        this.onTabChange = options.onTabChange || null;
        this.onLayoutModeChange = options.onLayoutModeChange || null;

        // 初始化防抖函數
        this.initDebounceHandlers();

        this.initUIElements();
    }

    /**
     * 初始化防抖處理器
     */
    UIManager.prototype.initDebounceHandlers = function() {
        // 為狀態指示器更新添加防抖
        this._debouncedUpdateStatusIndicator = Utils.DOM.debounce(
            this._originalUpdateStatusIndicator.bind(this),
            100,
            false
        );

        // 為狀態指示器元素更新添加防抖
        this._debouncedUpdateStatusIndicatorElement = Utils.DOM.debounce(
            this._originalUpdateStatusIndicatorElement.bind(this),
            50,
            false
        );
    };

    /**
     * 初始化 UI 元素
     */
    UIManager.prototype.initUIElements = function() {
        // 基本 UI 元素
        this.connectionIndicator = Utils.safeQuerySelector('#connectionIndicator');
        this.connectionText = Utils.safeQuerySelector('#connectionText');

        // 頁籤相關元素
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContents = document.querySelectorAll('.tab-content');

        // 回饋相關元素
        this.submitBtn = Utils.safeQuerySelector('#submitBtn');

        // 初始化 Mermaid 圖表庫
        this.initMermaid();

        console.log('✅ UI 元素初始化完成');
    };

    /**
     * 初始化頁籤功能
     */
    UIManager.prototype.initTabs = function() {
        const self = this;
        
        // 設置頁籤點擊事件
        this.tabButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const tabName = button.getAttribute('data-tab');
                self.switchTab(tabName);
            });
        });

        // 根據佈局模式確定初始頁籤
        let initialTab = this.currentTab;
        if (this.layoutMode.startsWith('combined')) {
            initialTab = 'combined';
        } else if (this.currentTab === 'combined') {
            initialTab = 'feedback';
        }

        // 設置初始頁籤
        this.setInitialTab(initialTab);
    };

    /**
     * 設置初始頁籤（不觸發保存）
     */
    UIManager.prototype.setInitialTab = function(tabName) {
        this.currentTab = tabName;
        this.updateTabDisplay(tabName);
        this.handleSpecialTabs(tabName);
        console.log('初始化頁籤: ' + tabName);
    };

    /**
     * 切換頁籤
     */
    UIManager.prototype.switchTab = function(tabName) {
        this.currentTab = tabName;
        this.updateTabDisplay(tabName);
        this.handleSpecialTabs(tabName);
        
        // 觸發回調
        if (this.onTabChange) {
            this.onTabChange(tabName);
        }
        
        console.log('切換到頁籤: ' + tabName);
    };

    /**
     * 更新頁籤顯示
     */
    UIManager.prototype.updateTabDisplay = function(tabName) {
        // 更新按鈕狀態
        this.tabButtons.forEach(function(button) {
            if (button.getAttribute('data-tab') === tabName) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // 更新內容顯示
        this.tabContents.forEach(function(content) {
            if (content.id === 'tab-' + tabName) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    };

    /**
     * 處理特殊頁籤
     */
    UIManager.prototype.handleSpecialTabs = function(tabName) {
        if (tabName === 'combined') {
            this.handleCombinedMode();
        }
    };

    /**
     * 處理合併模式
     */
    UIManager.prototype.handleCombinedMode = function() {
        console.log('切換到組合模式');
        
        // 確保合併模式的佈局樣式正確應用
        const combinedTab = Utils.safeQuerySelector('#tab-combined');
        if (combinedTab) {
            combinedTab.classList.remove('combined-vertical', 'combined-horizontal');
            if (this.layoutMode === 'combined-vertical') {
                combinedTab.classList.add('combined-vertical');
            } else if (this.layoutMode === 'combined-horizontal') {
                combinedTab.classList.add('combined-horizontal');
            }
        }
    };

    /**
     * 更新頁籤可見性
     */
    UIManager.prototype.updateTabVisibility = function() {
        const combinedTab = document.querySelector('.tab-button[data-tab="combined"]');
        const feedbackTab = document.querySelector('.tab-button[data-tab="feedback"]');
        const summaryTab = document.querySelector('.tab-button[data-tab="summary"]');

        // 只使用合併模式：顯示合併模式頁籤，隱藏回饋和AI摘要頁籤
        if (combinedTab) combinedTab.style.display = 'inline-block';
        if (feedbackTab) feedbackTab.style.display = 'none';
        if (summaryTab) summaryTab.style.display = 'none';
    };

    /**
     * 設置回饋狀態
     */
    UIManager.prototype.setFeedbackState = function(state, sessionId) {
        const previousState = this.feedbackState;
        this.feedbackState = state;

        if (sessionId) {
            console.log('🔄 會話 ID: ' + sessionId.substring(0, 8) + '...');
        }

        console.log('📊 狀態變更: ' + previousState + ' → ' + state);
        this.updateUIState();
        this.updateStatusIndicator();
    };

    /**
     * 更新 UI 狀態
     */
    UIManager.prototype.updateUIState = function() {
        this.updateSubmitButton();
        this.updateFeedbackInputs();
        this.updateImageUploadAreas();
    };

    /**
     * 更新提交按鈕狀態
     */
    UIManager.prototype.updateSubmitButton = function() {
        const submitButtons = [
            Utils.safeQuerySelector('#submitBtn')
        ].filter(function(btn) { return btn !== null; });

        const self = this;
        submitButtons.forEach(function(button) {
            if (!button) return;

            switch (self.feedbackState) {
                case Utils.CONSTANTS.FEEDBACK_WAITING:
                    button.textContent = window.i18nManager ? window.i18nManager.t('buttons.submit') : '提交回饋';
                    button.className = 'btn btn-primary';
                    button.disabled = false;
                    break;
                case Utils.CONSTANTS.FEEDBACK_PROCESSING:
                    button.textContent = window.i18nManager ? window.i18nManager.t('buttons.processing') : '處理中...';
                    button.className = 'btn btn-secondary';
                    button.disabled = true;
                    break;
                case Utils.CONSTANTS.FEEDBACK_SUBMITTED:
                    button.textContent = window.i18nManager ? window.i18nManager.t('buttons.submitted') : '已提交';
                    button.className = 'btn btn-success';
                    button.disabled = true;
                    break;
            }
        });
    };

    /**
     * 更新回饋輸入框狀態
     */
    UIManager.prototype.updateFeedbackInputs = function() {
        const feedbackInput = Utils.safeQuerySelector('#combinedFeedbackText');
        const canInput = this.feedbackState === Utils.CONSTANTS.FEEDBACK_WAITING;

        if (feedbackInput) {
            feedbackInput.disabled = !canInput;
        }
    };

    /**
     * 更新圖片上傳區域狀態
     */
    UIManager.prototype.updateImageUploadAreas = function() {
        const uploadAreas = [
            Utils.safeQuerySelector('#feedbackImageUploadArea'),
            Utils.safeQuerySelector('#combinedImageUploadArea')
        ].filter(function(area) { return area !== null; });

        const canUpload = this.feedbackState === Utils.CONSTANTS.FEEDBACK_WAITING;
        uploadAreas.forEach(function(area) {
            if (canUpload) {
                area.classList.remove('disabled');
            } else {
                area.classList.add('disabled');
            }
        });
    };

    /**
     * 更新狀態指示器（原始版本，供防抖使用）
     */
    UIManager.prototype._originalUpdateStatusIndicator = function() {
        const feedbackStatusIndicator = Utils.safeQuerySelector('#feedbackStatusIndicator');
        const combinedStatusIndicator = Utils.safeQuerySelector('#combinedFeedbackStatusIndicator');

        const statusInfo = this.getStatusInfo();

        if (feedbackStatusIndicator) {
            this._originalUpdateStatusIndicatorElement(feedbackStatusIndicator, statusInfo);
        }

        if (combinedStatusIndicator) {
            this._originalUpdateStatusIndicatorElement(combinedStatusIndicator, statusInfo);
        }

        // 減少重複日誌：只在狀態真正改變時記錄
        if (!this._lastStatusInfo || this._lastStatusInfo.status !== statusInfo.status) {
            console.log('✅ 狀態指示器已更新: ' + statusInfo.status + ' - ' + statusInfo.title);
            this._lastStatusInfo = statusInfo;
        }
    };

    /**
     * 更新狀態指示器（防抖版本）
     */
    UIManager.prototype.updateStatusIndicator = function() {
        if (this._debouncedUpdateStatusIndicator) {
            this._debouncedUpdateStatusIndicator();
        } else {
            // 回退到原始方法（防抖未初始化時）
            this._originalUpdateStatusIndicator();
        }
    };

    /**
     * 獲取狀態信息
     */
    UIManager.prototype.getStatusInfo = function() {
        let icon, title, message, status;

        switch (this.feedbackState) {
            case Utils.CONSTANTS.FEEDBACK_WAITING:
                icon = '⏳';
                title = window.i18nManager ? window.i18nManager.t('status.waiting.title') : '等待回饋';
                message = window.i18nManager ? window.i18nManager.t('status.waiting.message') : '請提供您的回饋意見';
                status = 'waiting';
                break;

            case Utils.CONSTANTS.FEEDBACK_PROCESSING:
                icon = '⚙️';
                title = window.i18nManager ? window.i18nManager.t('status.processing.title') : '處理中';
                message = window.i18nManager ? window.i18nManager.t('status.processing.message') : '正在提交您的回饋...';
                status = 'processing';
                break;

            case Utils.CONSTANTS.FEEDBACK_SUBMITTED:
                const timeStr = this.lastSubmissionTime ?
                    new Date(this.lastSubmissionTime).toLocaleTimeString() : '';
                icon = '✅';
                title = window.i18nManager ? window.i18nManager.t('status.submitted.title') : '回饋已提交';
                message = window.i18nManager ? window.i18nManager.t('status.submitted.message') : '等待下次 MCP 調用';
                if (timeStr) {
                    message += ' (' + timeStr + ')';
                }
                status = 'submitted';
                break;

            default:
                icon = '⏳';
                title = window.i18nManager ? window.i18nManager.t('status.waiting.title') : '等待回饋';
                message = window.i18nManager ? window.i18nManager.t('status.waiting.message') : '請提供您的回饋意見';
                status = 'waiting';
        }

        return { icon: icon, title: title, message: message, status: status };
    };

    /**
     * 更新單個狀態指示器元素（原始版本，供防抖使用）
     */
    UIManager.prototype._originalUpdateStatusIndicatorElement = function(element, statusInfo) {
        if (!element) return;

        // 更新狀態類別
        element.className = 'feedback-status-indicator status-' + statusInfo.status;
        element.style.display = 'block';

        // 更新標題
        const titleElement = element.querySelector('.status-title');
        if (titleElement) {
            titleElement.textContent = statusInfo.icon + ' ' + statusInfo.title;
        }

        // 更新訊息
        const messageElement = element.querySelector('.status-message');
        if (messageElement) {
            messageElement.textContent = statusInfo.message;
        }

        // 減少重複日誌：只記錄元素 ID 變化
        if (element.id) {
            console.log('🔧 已更新狀態指示器: ' + element.id + ' -> ' + statusInfo.status);
        }
    };

    /**
     * 更新單個狀態指示器元素（防抖版本）
     */
    UIManager.prototype.updateStatusIndicatorElement = function(element, statusInfo) {
        if (this._debouncedUpdateStatusIndicatorElement) {
            this._debouncedUpdateStatusIndicatorElement(element, statusInfo);
        } else {
            // 回退到原始方法（防抖未初始化時）
            this._originalUpdateStatusIndicatorElement(element, statusInfo);
        }
    };

    /**
     * 更新連接狀態
     */
    UIManager.prototype.updateConnectionStatus = function(status, text) {
        if (this.connectionIndicator) {
            this.connectionIndicator.className = 'connection-indicator ' + status;
        }
        if (this.connectionText) {
            this.connectionText.textContent = text;
        }
    };

    /**
     * 安全地渲染 Markdown 內容
     */
    UIManager.prototype.renderMarkdownSafely = function(content) {
        try {
            // 檢查 marked 和 DOMPurify 是否可用
            if (typeof window.marked === 'undefined' || typeof window.DOMPurify === 'undefined') {
                console.warn('⚠️ Markdown 庫未載入，使用純文字顯示');
                return this.escapeHtml(content);
            }

            // 配置 marked 使用自定義 renderer 來處理 mermaid
            const renderer = new marked.Renderer();
            const originalCode = renderer.code.bind(renderer);

            renderer.code = function(code, language) {
                // 如果是 mermaid 語言，保留原始格式以便後續渲染
                if (language === 'mermaid') {
                    return '<pre><code class="language-mermaid">' + code + '</code></pre>';
                }
                // 其他代碼塊使用原始 renderer
                return originalCode(code, language);
            };

            // 使用 marked 解析 Markdown，帶自定義 renderer
            const htmlContent = window.marked.parse(content, { renderer: renderer });

            // 使用 DOMPurify 清理 HTML，添加 mermaid 和快速选项占位符支援
            const cleanHtml = window.DOMPurify.sanitize(htmlContent, {
                ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'blockquote', 'a', 'hr', 'del', 's', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'div', 'span', 'svg', 'g', 'path', 'rect', 'circle', 'line', 'text', 'tspan', 'polygon', 'polyline', 'ellipse', 'marker', 'defs', 'clipPath', 'use', 'foreignObject'],
                ALLOWED_ATTR: ['href', 'title', 'class', 'align', 'style', 'id', 'viewBox', 'width', 'height', 'xmlns', 'fill', 'stroke', 'stroke-width', 'd', 'transform', 'x', 'y', 'cx', 'cy', 'r', 'rx', 'ry', 'x1', 'y1', 'x2', 'y2', 'points', 'marker-end', 'marker-start', 'font-size', 'font-family', 'text-anchor', 'dominant-baseline', 'clip-path', 'xlink:href', 'data-quick-option-id'],
                ALLOW_DATA_ATTR: true,
                KEEP_CONTENT: true
            });

            return cleanHtml;
        } catch (error) {
            console.error('❌ Markdown 渲染失敗:', error);
            return this.escapeHtml(content);
        }
    };

    /**
     * 初始化 Mermaid 圖表庫
     */
    UIManager.prototype.initMermaid = function() {
        if (typeof window.mermaid === 'undefined') {
            console.warn('⚠️ Mermaid 庫未載入');
            return false;
        }

        try {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: 'dark',
                securityLevel: 'loose',
                fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    useMaxWidth: true,
                    wrap: true
                },
                gantt: {
                    useMaxWidth: true
                }
            });
            console.log('✅ Mermaid 已初始化');
            return true;
        } catch (error) {
            console.error('❌ Mermaid 初始化失敗:', error);
            return false;
        }
    };

    /**
     * 渲染 Mermaid 圖表
     * @param {HTMLElement} container - 包含 mermaid 代碼塊的容器
     */
    UIManager.prototype.renderMermaidDiagrams = function(container) {
        if (!container || typeof window.mermaid === 'undefined') {
            return;
        }

        try {
            // 查找所有 mermaid 代碼塊 - 支持多種選擇器
            var codeBlocks = container.querySelectorAll('pre code.language-mermaid, code.language-mermaid, pre.mermaid, div.mermaid');

            if (codeBlocks.length === 0) {
                console.log('🔍 未找到 mermaid 代碼塊');
                return;
            }

            console.log('📊 找到 ' + codeBlocks.length + ' 個 Mermaid 圖表');

            var self = this;
            codeBlocks.forEach(function(codeBlock, index) {
                try {
                    var mermaidCode;
                    var preElement;

                    // 獲取 mermaid 代碼
                    if (codeBlock.tagName === 'CODE') {
                        mermaidCode = codeBlock.textContent || codeBlock.innerText;
                        preElement = codeBlock.closest('pre') || codeBlock.parentElement;
                    } else if (codeBlock.classList.contains('mermaid')) {
                        // 如果是 div.mermaid 或 pre.mermaid，直接獲取文本內容
                        mermaidCode = codeBlock.textContent || codeBlock.innerText;
                        preElement = codeBlock;
                    }

                    if (!mermaidCode || !preElement) {
                        console.warn('⚠️ 無法獲取 mermaid 代碼或元素', codeBlock);
                        return;
                    }

                    console.log('📝 Mermaid 代碼 ' + (index + 1) + ':', mermaidCode.substring(0, 50) + '...');

                    // 創建新的容器
                    var mermaidContainer = document.createElement('div');
                    mermaidContainer.className = 'mermaid-diagram';
                    mermaidContainer.id = 'mermaid-diagram-' + Date.now() + '-' + index;

                    // 替換原始代碼塊
                    if (preElement && preElement.parentNode) {
                        preElement.parentNode.replaceChild(mermaidContainer, preElement);
                    }

                    // 使用 mermaid 渲染
                    window.mermaid.render(mermaidContainer.id + '-svg', mermaidCode).then(function(result) {
                        // 創建圖表包裝器，用於放大功能
                        var svgWrapper = document.createElement('div');
                        svgWrapper.className = 'mermaid-svg-wrapper';
                        svgWrapper.innerHTML = result.svg;

                        // 創建圖表工具條
                        var toolBar = document.createElement('div');
                        toolBar.className = 'mermaid-toolbar';

                        // 創建放大按鈕
                        var expandBtn = document.createElement('button');
                        expandBtn.className = 'mermaid-expand-btn';
                        expandBtn.title = '放大顯示';
                        expandBtn.innerHTML = '🔍 放大';
                        expandBtn.addEventListener('click', function() {
                            self.showMermaidFullscreen(mermaidContainer.id, result.svg);
                        });

                        toolBar.appendChild(expandBtn);

                        // 清空容器並添加工具條和SVG包裝器
                        mermaidContainer.innerHTML = '';
                        mermaidContainer.appendChild(toolBar);
                        mermaidContainer.appendChild(svgWrapper);

                        console.log('✅ Mermaid 圖表 ' + (index + 1) + ' 渲染成功');
                    }).catch(function(error) {
                        console.error('❌ Mermaid 圖表 ' + (index + 1) + ' 渲染失敗:', error);
                        // 顯示錯誤訊息和原始代碼
                        mermaidContainer.innerHTML = '<div class="mermaid-error">' +
                            '<p>⚠️ 圖表渲染失敗</p>' +
                            '<pre><code>' + self.escapeHtml(mermaidCode) + '</code></pre>' +
                            '</div>';
                    });
                } catch (error) {
                    console.error('❌ 處理 Mermaid 代碼塊時發生錯誤:', error);
                }
            });
        } catch (error) {
            console.error('❌ 渲染 Mermaid 圖表時發生錯誤:', error);
        }
    };

    /**
     * 顯示 Mermaid 圖表全屏/放大視圖
     */
    UIManager.prototype.showMermaidFullscreen = function(diagramId, svgHtml) {
        // 創建模態框背景
        var backdrop = document.createElement('div');
        backdrop.className = 'mermaid-fullscreen-backdrop';
        backdrop.addEventListener('click', function(e) {
            if (e.target === backdrop) {
                backdrop.remove();
            }
        });

        // 創建模態框容器
        var modal = document.createElement('div');
        modal.className = 'mermaid-fullscreen-modal';

        // 創建關閉按鈕
        var closeBtn = document.createElement('button');
        closeBtn.className = 'mermaid-fullscreen-close';
        closeBtn.innerHTML = '✕';
        closeBtn.title = '關閉';
        closeBtn.addEventListener('click', function() {
            backdrop.remove();
        });

        // 創建圖表內容
        var content = document.createElement('div');
        content.className = 'mermaid-fullscreen-content';
        content.innerHTML = svgHtml;

        // 組合模態框
        modal.appendChild(closeBtn);
        modal.appendChild(content);
        backdrop.appendChild(modal);

        // 添加到頁面
        document.body.appendChild(backdrop);

        // 添加 ESC 鍵關閉功能
        var escKeyListener = function(e) {
            if (e.key === 'Escape') {
                backdrop.remove();
                document.removeEventListener('keydown', escKeyListener);
            }
        };
        document.addEventListener('keydown', escKeyListener);

        console.log('🔍 已打開 Mermaid 圖表全屏視圖');
    };

    /**
     * HTML 轉義函數
     */
    UIManager.prototype.escapeHtml = function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    /**
     * 更新 AI 摘要內容
     */
    UIManager.prototype.updateAISummaryContent = function(summary) {
        console.log('📝 更新 AI 摘要內容...', '內容長度:', summary ? summary.length : 'undefined');
        console.log('📝 原始內容前100字符:', summary ? summary.substring(0, 100) : 'undefined');
        // 檢查是否包含 <options> 或 <options ...>（帶屬性）
        var hasOptions = summary ? (summary.includes('<options>') || summary.includes('<options ')) : false;
        console.log('📝 是否包含 <options>:', hasOptions);
        console.log('📝 marked 可用:', typeof window.marked !== 'undefined');
        console.log('📝 DOMPurify 可用:', typeof window.DOMPurify !== 'undefined');

        // 解析快速選項
        var quickOptionGroups = this.parseQuickOptions(summary);
        console.log('📝 快速選項組數:', quickOptionGroups.length);
        if (quickOptionGroups.length > 0) {
            console.log('📝 第一組選項:', quickOptionGroups[0]);
        }

        // 使用自定义 span 标签作为占位符（不会被 DOMPurify 过滤）
        var contentWithPlaceholders = summary;
        var placeholderMap = {};

        for (var i = 0; i < quickOptionGroups.length; i++) {
            var placeholder = '<span data-quick-option-id="' + i + '"></span>';
            placeholderMap[i] = quickOptionGroups[i];
            contentWithPlaceholders = contentWithPlaceholders.replace(quickOptionGroups[i].fullMatch, placeholder);
        }

        // 渲染 Markdown 內容（span 占位符會保留）
        var renderedContent = this.renderMarkdownSafely(contentWithPlaceholders);
        console.log('📝 渲染後內容長度:', renderedContent ? renderedContent.length : 'undefined');

        // 將占位符替換為實際的快速選項 HTML
        var finalContent = renderedContent;
        for (var i = 0; i < quickOptionGroups.length; i++) {
            var placeholder = '<span data-quick-option-id="' + i + '"></span>';
            var group = placeholderMap[i];
            var quickOptionsHtml = this.renderQuickOptionsHtml([group]);
            finalContent = finalContent.replace(placeholder, quickOptionsHtml);
        }

        var summaryContent = Utils.safeQuerySelector('#summaryContent');
        if (summaryContent) {
            summaryContent.innerHTML = finalContent;
            // 渲染 Mermaid 圖表
            this.renderMermaidDiagrams(summaryContent);
            console.log('✅ 已更新分頁模式摘要內容（Markdown 渲染）');
        } else {
            console.warn('⚠️ 找不到 #summaryContent 元素');
        }

        var combinedSummaryContent = Utils.safeQuerySelector('#combinedSummaryContent');
        if (combinedSummaryContent) {
            combinedSummaryContent.innerHTML = finalContent;
            // 渲染 Mermaid 圖表
            this.renderMermaidDiagrams(combinedSummaryContent);
            console.log('✅ 已更新合併模式摘要內容（Markdown 渲染）');
        } else {
            console.warn('⚠️ 找不到 #combinedSummaryContent 元素');
        }

        // 綁定快速選項事件
        if (quickOptionGroups.length > 0) {
            this.bindQuickOptionEvents();
            console.log('✅ 快速選項事件已綁定');
        }
    };

    /**
     * 重置回饋表單
     * @param {boolean} clearText - 是否清空文字內容，預設為 false
     */
    UIManager.prototype.resetFeedbackForm = function(clearText) {
        console.log('🔄 重置回饋表單...');

        // 根據參數決定是否清空回饋輸入
        const feedbackInput = Utils.safeQuerySelector('#combinedFeedbackText');
        if (feedbackInput) {
            if (clearText === true) {
                feedbackInput.value = '';
                console.log('📝 已清空文字內容');
            }
            // 只有在等待狀態才啟用輸入框
            const canInput = this.feedbackState === Utils.CONSTANTS.FEEDBACK_WAITING;
            feedbackInput.disabled = !canInput;
        }

        // 重新啟用提交按鈕
        const submitButtons = [
            Utils.safeQuerySelector('#submitBtn')
        ].filter(function(btn) { return btn !== null; });

        submitButtons.forEach(function(button) {
            button.disabled = false;
            const defaultText = window.i18nManager ? window.i18nManager.t('buttons.submit') : '提交回饋';
            button.textContent = button.getAttribute('data-original-text') || defaultText;
        });

        console.log('✅ 回饋表單重置完成');
    };

    /**
     * 應用佈局模式
     */
    UIManager.prototype.applyLayoutMode = function(layoutMode) {
        this.layoutMode = layoutMode;
        
        const expectedClassName = 'layout-' + layoutMode;
        if (document.body.className !== expectedClassName) {
            console.log('應用佈局模式: ' + layoutMode);
            document.body.className = expectedClassName;
        }

        this.updateTabVisibility();
        
        // 如果當前頁籤不是合併模式，則切換到合併模式頁籤
        if (this.currentTab !== 'combined') {
            this.currentTab = 'combined';
        }
        
        // 觸發回調
        if (this.onLayoutModeChange) {
            this.onLayoutModeChange(layoutMode);
        }
    };

    /**
     * 獲取當前頁籤
     */
    UIManager.prototype.getCurrentTab = function() {
        return this.currentTab;
    };

    /**
     * 獲取當前回饋狀態
     */
    UIManager.prototype.getFeedbackState = function() {
        return this.feedbackState;
    };

    /**
     * 設置最後提交時間
     */
    UIManager.prototype.setLastSubmissionTime = function(timestamp) {
        this.lastSubmissionTime = timestamp;
        this.updateStatusIndicator();
    };

    // ===== 快速選項功能 =====

    /**
     * 解析快速選項 XML
     * 支援多個 <options> 區塊
     * 支援標籤屬性如 <options title="..."> 和 <option key="A">
     */
    UIManager.prototype.parseQuickOptions = function(content) {
        var groups = [];
        // 支援帶屬性的 <options> 標籤，如 <options title="標題">
        var optionsRegex = /<options([^>]*)>([\s\S]*?)<\/options>/gi;
        var match;
        var groupIndex = 1;

        while ((match = optionsRegex.exec(content)) !== null) {
            var optionsAttrs = match[1];
            var optionsContent = match[2];
            var options = [];

            // 解析 options 的 title 屬性
            var titleMatch = optionsAttrs.match(/title\s*=\s*["']([^"']*)["']/i);
            var groupTitle = titleMatch ? titleMatch[1] : null;

            // 每次创建新的正则表达式，避免状态问题
            // 支援帶屬性的 <option> 標籤，如 <option key="A" description="...">
            var optionRegex = /<option([^>]*)>([\s\S]*?)<\/option>/gi;
            var optionMatch;

            while ((optionMatch = optionRegex.exec(optionsContent)) !== null) {
                var optionAttrs = optionMatch[1];
                var optionText = optionMatch[2].trim();

                // 解析 option 的 description 屬性
                var descMatch = optionAttrs.match(/description\s*=\s*["']([^"']*)["']/i);
                var description = descMatch ? descMatch[1] : null;

                // 解析 option 的 key 屬性
                var keyMatch = optionAttrs.match(/key\s*=\s*["']([^"']*)["']/i);
                var key = keyMatch ? keyMatch[1] : null;

                options.push({
                    text: optionText,
                    description: description,
                    key: key
                });
            }

            if (options.length > 0) {
                groups.push({
                    index: groupIndex,
                    title: groupTitle,
                    options: options,
                    fullMatch: match[0]
                });
                groupIndex++;
            }
        }

        return groups;
    };

    /**
     * 渲染快速選項 HTML
     */
    UIManager.prototype.renderQuickOptionsHtml = function(groups) {
        if (!groups || groups.length === 0) return '';

        var html = '<div class="quick-options-container">';

        for (var g = 0; g < groups.length; g++) {
            var group = groups[g];
            html += '<div class="quick-options-group" data-group="' + group.index + '">';

            // 使用自定義 title 或預設標題（支援 i18n）
            var defaultTitle = window.i18nManager
                ? window.i18nManager.t('quickOptions.groupTitle', { index: group.index })
                : ('選項組 ' + group.index);
            var groupTitle = group.title || defaultTitle;
            html += '<div class="quick-options-group-title">' + this.escapeHtml(groupTitle) + '</div>';

            for (var i = 0; i < group.options.length; i++) {
                var option = group.options[i];
                var optionId = 'quick-option-' + group.index + '-' + i;
                var optionText = typeof option === 'string' ? option : option.text;
                var optionDesc = typeof option === 'object' ? option.description : null;

                html += '<div class="quick-option-row" data-group="' + group.index + '" data-index="' + i + '">';
                html += '<input type="checkbox" id="' + optionId + '" class="quick-option-checkbox" data-group="' + group.index + '" data-value="' + this.escapeHtml(optionText) + '">';
                html += '<div class="quick-option-content">';
                html += '<div class="quick-option-label">' + this.escapeHtml(optionText) + '</div>';
                if (optionDesc) {
                    html += '<div class="quick-option-description">' + this.escapeHtml(optionDesc) + '</div>';
                }
                html += '</div>';
                html += '</div>';
            }

            html += '</div>';
        }

        html += '</div>';
        return html;
    };

    /**
     * 綁定快速選項事件
     */
    UIManager.prototype.bindQuickOptionEvents = function() {
        var self = this;
        var container = document.getElementById('combinedSummaryContent');
        if (!container) return;

        // 綁定選項行點擊事件
        var optionRows = container.querySelectorAll('.quick-option-row');
        optionRows.forEach(function(row) {
            row.addEventListener('click', function(e) {
                // 如果點擊的是 checkbox 本身，不需要額外處理
                if (e.target.classList.contains('quick-option-checkbox')) {
                    self.handleQuickOptionChange();
                    return;
                }
                // 點擊行的其他區域，切換 checkbox
                var checkbox = row.querySelector('.quick-option-checkbox');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    self.handleQuickOptionChange();
                }
            });
        });

        // 綁定 XML 模式切換
        var xmlModeCheckbox = document.getElementById('quickOptionsXmlMode');
        if (xmlModeCheckbox) {
            xmlModeCheckbox.addEventListener('change', function() {
                self.handleQuickOptionChange();
            });
        }
    };

    /**
     * 處理快速選項變更
     */
    UIManager.prototype.handleQuickOptionChange = function() {
        var previewContainer = document.getElementById('quickOptionsPreview');
        var previewContent = document.getElementById('quickOptionsPreviewContent');
        var xmlModeCheckbox = document.getElementById('quickOptionsXmlMode');

        var isXmlMode = xmlModeCheckbox ? xmlModeCheckbox.checked : false;
        console.log('🔍 handleQuickOptionChange - XML 模式:', isXmlMode);

        // 收集所有選中的選項
        var checkboxes = document.querySelectorAll('.quick-option-checkbox:checked');
        var groupedSelections = {};
        var groups = [];

        checkboxes.forEach(function(cb) {
            var groupNum = cb.getAttribute('data-group');
            var value = cb.getAttribute('data-value');
            if (!groupedSelections[groupNum]) {
                groupedSelections[groupNum] = [];
                groups.push(groupNum);
            }
            groupedSelections[groupNum].push(value);
        });

        var hasSelections = groups.length > 0;

        // 顯示或隱藏預覽區域
        if (previewContainer) {
            previewContainer.style.display = hasSelections ? 'block' : 'none';
        }

        // 更新預覽區域（不自動更新文本輸入框）
        if (hasSelections && previewContent) {
            this.updateQuickOptionsPreview(previewContent, groupedSelections, groups, isXmlMode);
        }
    };

    /**
     * 構建文本模式內容
     */
    UIManager.prototype.buildTextContent = function(groupedSelections, groups) {
        var lines = [];
        for (var i = 0; i < groups.length; i++) {
            var groupNum = groups[i];
            var selections = groupedSelections[groupNum];
            for (var j = 0; j < selections.length; j++) {
                lines.push('[' + groupNum + '] ' + selections[j]);
            }
        }
        return lines.join('\n');
    };

    /**
     * 構建 XML 模式內容
     */
    UIManager.prototype.buildXmlContent = function(groupedSelections, groups) {
        var xml = '';
        for (var i = 0; i < groups.length; i++) {
            var groupNum = groups[i];
            var selections = groupedSelections[groupNum];
            xml += '<options group="' + groupNum + '">\n';
            for (var j = 0; j < selections.length; j++) {
                xml += '  <option>' + selections[j] + '</option>\n';
            }
            xml += '</options>\n';
        }
        return xml.trim();
    };

    /**
     * 更新快速選項預覽區域
     */
    UIManager.prototype.updateQuickOptionsPreview = function(container, groupedSelections, groups, isXmlMode) {
        console.log('🔧 updateQuickOptionsPreview - isXmlMode:', isXmlMode);
        var self = this;

        if (isXmlMode) {
            // XML 模式：顯示可編輯的 textarea
            var xmlContent = this.buildXmlContent(groupedSelections, groups);
            var textarea = container.querySelector('.preview-xml-textarea');

            if (!textarea) {
                container.innerHTML = '';
                textarea = document.createElement('textarea');
                textarea.className = 'preview-xml-textarea';
                textarea.id = 'quickOptionsXmlTextarea';
                textarea.placeholder = '可編輯 XML 內容...';
                container.appendChild(textarea);
            }

            // 只有當自動生成的內容改變時才更新
            if (textarea.dataset.autoGenerated !== xmlContent) {
                textarea.value = xmlContent;
                textarea.dataset.autoGenerated = xmlContent;
            }
        } else {
            // 文本模式：為每個選項顯示帶備註輸入框的預覽
            var html = '<div class="preview-items">';

            for (var i = 0; i < groups.length; i++) {
                var groupNum = groups[i];
                var selections = groupedSelections[groupNum];
                for (var j = 0; j < selections.length; j++) {
                    var optionValue = selections[j];
                    var inputId = 'note-' + groupNum + '-' + j;
                    // 保留現有的備註值
                    var existingInput = container.querySelector('#' + inputId);
                    var existingNote = existingInput ? existingInput.value : '';
                    var notePlaceholder = window.i18nManager
                        ? window.i18nManager.t('quickOptions.notePlaceholder')
                        : '備註...';

                    html += '<div class="preview-item">';
                    html += '<span class="preview-item-text">[' + groupNum + '] ' + this.escapeHtml(optionValue) + '</span>';
                    html += '<input type="text" id="' + inputId + '" class="preview-item-note" placeholder="' + this.escapeHtml(notePlaceholder) + '" value="' + this.escapeHtml(existingNote) + '" data-group="' + groupNum + '" data-value="' + this.escapeHtml(optionValue) + '">';
                    html += '</div>';
                }
            }

            html += '</div>';
            container.innerHTML = html;
        }
    };

    /**
     * 從預覽區域的備註更新回饋輸入框
     */
    UIManager.prototype.updateFeedbackFromPreview = function() {
        var feedbackInput = document.getElementById('combinedFeedbackText');
        var previewContent = document.getElementById('quickOptionsPreviewContent');
        if (!feedbackInput || !previewContent) return;

        var lines = [];
        var items = previewContent.querySelectorAll('.preview-item');
        items.forEach(function(item) {
            var text = item.querySelector('.preview-item-text');
            var noteInput = item.querySelector('.preview-item-note');
            if (text) {
                var line = text.textContent;
                if (noteInput && noteInput.value.trim()) {
                    line += ' - ' + noteInput.value.trim();
                }
                lines.push(line);
            }
        });

        feedbackInput.value = lines.join('\n');
    };

    /**
     * 獲取快速選項的最終內容（用於提交）
     */
    UIManager.prototype.getQuickOptionsContent = function() {
        var xmlModeCheckbox = document.getElementById('quickOptionsXmlMode');
        var isXmlMode = xmlModeCheckbox ? xmlModeCheckbox.checked : false;

        if (isXmlMode) {
            // XML 模式：直接返回 XML 內容
            var textarea = document.getElementById('quickOptionsXmlTextarea');
            return textarea ? textarea.value : '';
        } else {
            // 文本模式：從預覽區域收集選項和備註
            var previewContent = document.getElementById('quickOptionsPreviewContent');
            if (!previewContent) return '';

            var lines = [];
            var items = previewContent.querySelectorAll('.preview-item');
            items.forEach(function(item) {
                var text = item.querySelector('.preview-item-text');
                var noteInput = item.querySelector('.preview-item-note');
                if (text) {
                    var line = text.textContent;
                    if (noteInput && noteInput.value.trim()) {
                        line += ' - ' + noteInput.value.trim();
                    }
                    lines.push(line);
                }
            });

            return lines.join('\n');
        }
    };

    // 將 UIManager 加入命名空間
    window.MCPFeedback.UIManager = UIManager;

    console.log('✅ UIManager 模組載入完成');

})();
