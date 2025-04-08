// Function to get URL parameters
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function formatIssueForDisplay(issue) {
    // First replace underscores with spaces
    let displayIssue = issue.replace(/_/g, " ");
    
    // Then replace "sk" with "신간" if it's at the beginning of the string
    displayIssue = displayIssue.replace(/^sk /i, "신간 ");
    
    return displayIssue;
}

function loadIssueScript(issue, callback) {
    const baseDir = isEnglishMode() ? 'support/index_en/' : 'support/index/';
    const fileName = encodeURIComponent(issue) + '.js';
    const script = document.createElement('script');
    script.src = baseDir + fileName;
    script.onload = () => {
        if (typeof window.ISSUE_DATA === 'undefined') {
            console.error('ISSUE_DATA not defined in file:', script.src);
            return;
        }
        callback(window.ISSUE_DATA);
        delete window.ISSUE_DATA; // clean up global namespace
    };
    script.onerror = () => {
        const contentDiv = document.getElementById('content');
        contentDiv.innerHTML = `
            <div class="error">
                <p>Could not load issue data for "${issue}".</p>
                <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
            </div>
        `;
    };
    document.body.appendChild(script);
}

// Check if English language mode is active
function isEnglishMode() {
    return getUrlParam('lang') === 'en';
}

// Function to create URLs that preserve the language parameter
function createUrl(base, params = {}) {
    const url = new URL(base, window.location.href);
    const urlParams = new URLSearchParams(window.location.search);
    
    // Copy existing language parameter if present
    if (isEnglishMode()) {
        url.searchParams.set('lang', 'en');
    }
    
    // Add all other parameters
    for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, value);
    }
    
    return url.toString();
}

function loadIssueScript(issue, callback) {
    const baseDir = isEnglishMode() ? 'support/index_en/' : 'support/index/';
    const fileName = encodeURIComponent(issue) + '.js';
    const script = document.createElement('script');
    script.src = baseDir + fileName;
    script.onload = () => {
        if (typeof window.ISSUE_DATA === 'undefined') {
            console.error('ISSUE_DATA not defined in file:', script.src);
            return;
        }
        const data = window.ISSUE_DATA;
        delete window.ISSUE_DATA;
        callback(data);
    };
    script.onerror = () => {
        const contentDiv = document.getElementById('content');
        contentDiv.innerHTML = `
            <div class="error">
                <p>Could not load issue data for "${issue}".</p>
                <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
            </div>
        `;
    };
    document.body.appendChild(script);
}

// Toggle language mode
function toggleLanguageMode() {
    const currentUrl = new URL(window.location.href);
    const params = new URLSearchParams(currentUrl.search);
    
    if (isEnglishMode()) {
        params.delete('lang');
    } else {
        params.set('lang', 'en');
    }
    
    currentUrl.search = params.toString();
    window.location.href = currentUrl.toString();
}

// Initialize language toggle
function initLanguageToggle() {
    const toggle = document.getElementById('language-toggle');
    if (toggle) {
        toggle.checked = isEnglishMode();
        toggle.addEventListener('change', toggleLanguageMode);
    }
    
    // Apply 'english-mode' class to body when in English mode
    if (isEnglishMode()) {
        document.body.classList.add('english-mode');
    }
}

function loadDataScript() {
    // No longer needed
}

// Get all unique issues sorted
function getAllSortedIssues() {
    if (typeof ISSUE_LIST !== 'undefined') {
        return ISSUE_LIST;
    }
    return [...new Set(ARTICLES.map(item => item.issue))].sort();
}

// Get adjacent issues (previous and next)
function getAdjacentIssues(currentIssue) {
    const allIssues = getAllSortedIssues();
    const currentIndex = allIssues.indexOf(currentIssue);
    
    return {
        prevIssue: currentIndex > 0 ? allIssues[currentIndex - 1] : null,
        nextIssue: currentIndex < allIssues.length - 1 ? allIssues[currentIndex + 1] : null
    };
}

// Function to find PDF path for a given issue
function getPdfPath(issueName) {
    if (typeof PDFS === 'undefined') return null;
    
    const normalized = issueName.normalize('NFD');
    const pdfInfo = PDFS.find(pdf => pdf.issue === normalized);
    return pdfInfo && pdfInfo.path ? pdfInfo.path : null;
}

// Function to process markdown-style bold text in English mode
function processBoldText(text) {
    if (!isEnglishMode()) return text;
    
    // Replace **text** with <strong>text</strong>
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Format the article content with proper formatting
function formatContent(content, type) {
    // Process bold text markup if in English mode
    const processedContent = processBoldText(content);
    
    // For poetry, preserve line breaks without paragraph spacing
    if (type === '시') {
        return `<div class="poetry">${processedContent}</div>`;
    }
    
    // For all other types, handle paragraphs
    return processedContent.split('\n').map(paragraph => {
        // Skip empty paragraphs
        if (paragraph.trim() === '') return '';
        return `<p>${paragraph}</p>`;
    }).join('');
}

// Display list of unique issues
function displayIssueList() {
    const contentDiv = document.getElementById('content');
    
    // Extract unique issues
    const uniqueIssues = getAllSortedIssues();
    
    let issueListHTML = ``;
    
    issueListHTML += `
        <div class="article-header">
            <div class="article-title">Korean Periodicals Archive</div>
        </div>
        <h2>Available Issues</h2>
        <ul class="issue-list">
    `;
    
    uniqueIssues.forEach(issue => {
        const pdfPath = getPdfPath(issue);
        const displayIssue = formatIssueForDisplay(issue); // Format the issue name for display
        
        issueListHTML += `
            <li>
                <div>
                    <a href="${createUrl('index.html', {issue: issue})}">${displayIssue}</a>
                    <a href="${createUrl('index.html', {issue: issue, all: 'yes'})}" class="all-link">Full View</a>
                    ${pdfPath ? `<span class="link-separator">|</span><a href="${pdfPath}" class="all-link" target="_blank">PDF</a>` : ''}
                </div>
            </li>
        `;
    });
    
    issueListHTML += '</ul>';
    contentDiv.innerHTML = issueListHTML;
}

// Display articles in a specific issue
function displayIssueArticles(issueName) {
    const contentDiv = document.getElementById('content');
    const showAll = getUrlParam('all') === 'yes';

    loadIssueScript(issueName, (issueArticles) => {
        const pdfPath = getPdfPath(issueName);
        const { prevIssue, nextIssue } = getAdjacentIssues(issueName);
        const displayIssueName = formatIssueForDisplay(issueName); // Format for display

        issueArticles.sort((a, b) => {
            const getFileNumber = (path) => {
                const matches = path.match(/\/(\d+)\.txt$/);
                return matches ? parseInt(matches[1], 10) : 0;
            };
            return getFileNumber(a.path) - getFileNumber(b.path);
        });

        if (issueArticles.length === 0) {
            contentDiv.innerHTML = `
                <div class="error">
                    <p>No articles found for issue "${displayIssueName}".</p>
                    <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
                </div>
            `;
            return;
        }

        if (showAll) {
            let allArticlesHTML = `
                <div class="article-header">
                    <div class="issue-title">
                        ${displayIssueName}
                        <a href="${createUrl('index.html', {issue: issueName})}" class="all-articles-link">List</a>
                        ${pdfPath ? `<a href="${pdfPath}" class="all-articles-link" target="_blank" style="margin-left: 10px;">PDF</a>` : ''}
                    </div>
                </div>
            `;

            issueArticles.forEach((article, index) => {
                const authorLinksHTML = article.author ? 
                    (isEnglishMode() ?
                        `<a href="${createUrl('index.html', {author: article.author})}" style="color: inherit; text-decoration: none;">${article.author}</a>` :
                        article.author.split(' ').map(name => 
                            `<a href="${createUrl('index.html', {author: name})}" style="color: inherit; text-decoration: none;">${name}</a>`
                        ).join(' ')
                    ) : 'Unknown';

                allArticlesHTML += `
                    <div class="article-container">
                        <div class="article-header">
                            <div class="article-title">${article.title}</div>
                            <div class="article-meta">
                                <div class="article-meta-row">
                                    ${article.author ? `<span class="meta-label">Author:</span> ${article.author} <span class="meta-separator">|</span>` : ''}
                                    <span class="meta-label">Type:</span> ${article.type || 'Other'}
                                </div>
                            </div>
                        </div>
                        <div class="article-content">${formatContent(article.content, article.type)}</div>
                    </div>
                `;

                if (index < issueArticles.length - 1) {
                    allArticlesHTML += `<hr class="article-separator" />`;
                }
            });

            allArticlesHTML += `<p><a href="${createUrl('index.html')}">&laquo; Back to all issues</a></p>`;
            contentDiv.innerHTML = allArticlesHTML;
        } else {
            let articleListHTML = `
                <div class="article-header">
                    <div class="issue-title">
                        ${displayIssueName}
                        <a href="${createUrl('index.html', {issue: issueName, all: 'yes'})}" class="all-articles-link">Full View</a>
                        ${pdfPath ? `<a href="${pdfPath}" class="all-articles-link" target="_blank" style="margin-left: 10px;">PDF</a>` : ''}
                    </div>
                </div>
                <ul class="article-list">
            `;

            issueArticles.forEach(article => {
                const authorLinksHTML = article.author || '';
                articleListHTML += `
                    <li>
                        <div class="article-list-title">
                            <a href="${createUrl('index.html', {path: article.path})}">${article.title}</a>
                        </div>
                        <div class="article-list-meta">
                            ${authorLinksHTML ? `${authorLinksHTML} <span class="meta-separator">|</span> ` : ''}
                            ${article.type || ''}
                        </div>
                    </li>
                `;
            });

            articleListHTML += `
                </ul>
                <p><a href="${createUrl('index.html')}">&laquo; Back to all issues</a></p>
                <div class="article-navigation">
                    <div class="nav-links">
                        <div></div>
                        <div class="nav-pagination">
                            ${prevIssue ?
                                `<a href="${createUrl('index.html', {issue: prevIssue})}" class="nav-link-prev">Previous Issue</a>` :
                                `<span class="nav-link-disabled">Previous Issue</span>`
                            }
                            ${nextIssue ?
                                `<a href="${createUrl('index.html', {issue: nextIssue})}" class="nav-link-next">Next Issue</a>` :
                                `<span class="nav-link-disabled">Next Issue</span>`
                            }
                        </div>
                    </div>
                </div>
            `;
            contentDiv.innerHTML = articleListHTML;
        }
    });
}

// Display a specific article
function displayArticle(articlePath) {
    const contentDiv = document.getElementById('content');
    const match = articlePath.match(/^(.+?)\//);
    if (!match) {
        contentDiv.innerHTML = `<div class="error">Invalid article path: ${articlePath}</div>`;
        return;
    }

    const issueName = match[1];

    loadIssueScript(issueName, (issueArticles) => {
        const article = issueArticles.find(item => item.path === articlePath);

        if (!article) {
            contentDiv.innerHTML = `
                <div class="error">
                    <p>The requested article "${articlePath}" could not be found.</p>
                    <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
                </div>
            `;
            return;
        }

        const pdfPath = getPdfPath(article.issue);
        const displayIssue = formatIssueForDisplay(article.issue); // Format for display

        issueArticles.sort((a, b) => {
            const getFileNumber = (path) => {
                const matches = path.match(/\/(\d+)\.txt$/);
                return matches ? parseInt(matches[1], 10) : 0;
            };
            return getFileNumber(a.path) - getFileNumber(b.path);
        });

        const currentIndex = issueArticles.findIndex(item => item.path === article.path);
        const prevArticle = currentIndex > 0 ? issueArticles[currentIndex - 1] : null;
        const nextArticle = currentIndex < issueArticles.length - 1 ? issueArticles[currentIndex + 1] : null;

        const { prevIssue, nextIssue } = getAdjacentIssues(article.issue);

        document.title = `${article.title} - Korean Periodicals Archive`;

        const hasExcessiveMetadata = 
            (article.date && article.date.includes('\n')) || 
            (article.author && article.author.includes('\n')) ||
            (article.magazine && article.magazine.includes('\n'));

        let articleHTML = '';

        if (hasExcessiveMetadata) {
            articleHTML = `
                <div class="article-header">
                    <div class="article-title">${article.title}</div>
                    <div class="article-meta">
                        <div><span class="meta-label">Issue:</span> 
                            <a href="${createUrl('index.html', {issue: article.issue})}" style="color: inherit; text-decoration: none;">
                                ${article.issue}
                            </a>
                            ${pdfPath ? `<a href="${pdfPath}" class="all-articles-link" target="_blank" style="margin-left: 10px; font-size: 0.8em;">PDF</a>` : ''}
                        </div>
                        ${article.type ? `
                        <div><span class="meta-label">Type:</span> 
                            <a href="${createUrl('index.html', {type: article.type})}" style="color: inherit; text-decoration: none;">
                                ${article.type}
                            </a>
                        </div>` : ''}
                    </div>
                    <div style="margin-top: 10px; color: #999; font-size: 0.9em;">
                        ${prevArticle ? 
                            `<a href="${createUrl('index.html', {path: prevArticle.path})}" style="color: #999; text-decoration: none; margin-right: 15px;">« Previous Article</a>` : 
                            prevIssue ? 
                                `<a href="${createUrl('index.html', {issue: prevIssue})}" style="color: #999; text-decoration: none; margin-right: 15px;">« Previous Issue</a>` :
                                ``
                        }
                        ${nextArticle ? 
                            `<a href="${createUrl('index.html', {path: nextArticle.path})}" style="color: #999; text-decoration: none;">Next Article »</a>` : 
                            nextIssue ? 
                                `<a href="${createUrl('index.html', {issue: nextIssue})}" style="color: #999; text-decoration: none;">Next Issue »</a>` :
                                ``
                        }
                    </div>
                </div>
            `;

            let combinedContent = article.content;

            if (article.author && article.author.includes('\n')) {
                combinedContent = `<div class="metadata-section"><strong>Author Information:</strong>\n${article.author}</div>\n\n${combinedContent}`;
            }

            if (article.date && article.date.includes('\n')) {
                combinedContent = `<div class="metadata-section"><strong>Additional Information:</strong>\n${article.date}</div>\n\n${combinedContent}`;
            }

            if (article.magazine && article.magazine.includes('\n')) {
                combinedContent = `<div class="metadata-section"><strong>Publication Information:</strong>\n${article.magazine}</div>\n\n${combinedContent}`;
            }

            articleHTML += `<div class="article-content">${formatContent(combinedContent, article.type)}</div>`;
        } else {
            const authorLinksHTML = article.author ? 
                (isEnglishMode() ? 
                    `<a href="${createUrl('index.html', {author: article.author})}" style="color: inherit; text-decoration: none;">${article.author}</a>` :
                    article.author.split(' ').map(name => 
                        `<a href="${createUrl('index.html', {author: name})}" style="color: inherit; text-decoration: none;">${name}</a>`
                    ).join(' ')
                ) : 'Unknown';

            articleHTML = `
                <div class="article-header">
                    <div class="article-title">${article.title}</div>
                    <div class="article-meta">
                        <div><span class="meta-label">Author:</span> ${article.author || 'Unknown'}</div>
                        <div><span class="meta-label">Publication:</span> ${article.magazine} (${article.date})</div>
                        <div><span class="meta-label">Type:</span> ${article.type || 'Other'}</div>
                        <div><span class="meta-label">Issue:</span> 
                            <a href="${createUrl('index.html', {issue: article.issue})}" style="color: inherit; text-decoration: none;">
                                ${displayIssue}
                            </a>
                            ${pdfPath ? `<a href="${pdfPath}" class="all-articles-link" target="_blank" style="margin-left: 10px; font-size: 0.8em;">PDF</a>` : ''}
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #999; font-size: 0.9em;">
                        ${prevArticle ? 
                            `<a href="${createUrl('index.html', {path: prevArticle.path})}" style="color: #999; text-decoration: none; margin-right: 15px;">« Previous Article</a>` : 
                            prevIssue ? 
                                `<a href="${createUrl('index.html', {issue: prevIssue})}" style="color: #999; text-decoration: none; margin-right: 15px;">« Previous Issue</a>` :
                                ``
                        }
                        ${nextArticle ? 
                            `<a href="${createUrl('index.html', {path: nextArticle.path})}" style="color: #999; text-decoration: none;">Next Article »</a>` : 
                            nextIssue ? 
                                `<a href="${createUrl('index.html', {issue: nextIssue})}" style="color: #999; text-decoration: none;">Next Issue »</a>` :
                                ``
                        }
                    </div>
                </div>
                <div class="article-content">${formatContent(article.content, article.type)}</div>
            `;
        }

        articleHTML += `
            <div class="article-navigation">
                <div class="nav-links">
                    <a href="${createUrl('index.html', {issue: article.issue})}" class="nav-link-issue">&laquo; Back to ${displayIssue}</a>
                    <div class="nav-pagination">
                        ${prevArticle ? 
                            `<a href="${createUrl('index.html', {path: prevArticle.path})}" class="nav-link-prev">Previous Article</a>` : 
                            prevIssue ? 
                                `<a href="${createUrl('index.html', {issue: prevIssue})}" class="nav-link-prev">Previous Issue</a>` :
                                `<span class="nav-link-disabled">Previous Article</span>`
                        }
                        ${nextArticle ? 
                            `<a href="${createUrl('index.html', {path: nextArticle.path})}" class="nav-link-next">Next Article</a>` : 
                            nextIssue ? 
                                `<a href="${createUrl('index.html', {issue: nextIssue})}" class="nav-link-next">Next Issue</a>` :
                                `<span class="nav-link-disabled">Next Article</span>`
                        }
                    </div>
                </div>
            </div>
        `;

        contentDiv.innerHTML = articleHTML;
    });
}

// Display articles by a specific author
// Update the displayAuthorArticles function
// Note: This function doesn't need to change its filtering behavior,
// since when in English mode, full names are used as the author parameter
function displayAuthorArticles(authorName) {
    const contentDiv = document.getElementById('content');
    
    // Filter articles by author
    const authorArticles = ARTICLES.filter(item => 
        item.author && item.author.includes(authorName)
    ).sort((a, b) => a.date.localeCompare(b.date) || a.title.localeCompare(b.title));
    
    if (authorArticles.length === 0) {
        contentDiv.innerHTML = `
            <div class="error">
                <p>No articles found by author "${authorName}".</p>
                <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
            </div>
        `;
        return;
    }
    
    let articleListHTML = `
        <div class="article-header">
            <div class="issue-title">Articles by ${authorName}</div>
        </div>
        <ul class="article-list">
    `;
    
    authorArticles.forEach(article => {
        // Get PDF path for this issue
        const pdfPath = getPdfPath(article.issue);
        
        articleListHTML += `
            <li>
                <div class="article-list-title">
                    <a href="${createUrl('index.html', {path: article.path})}">${article.title}</a>
                </div>
                <div class="article-list-meta">
                    <a href="${createUrl('index.html', {issue: article.issue})}">${article.issue}</a>
                    ${pdfPath ? `<a href="${pdfPath}" class="pdf-link" target="_blank" style="font-size: 0.8em; padding: 1px 4px;">PDF</a>` : ''}
                    ${article.type ? `<a href="${createUrl('index.html', {type: article.type})}">${article.type}</a>` : ''}
                </div>
            </li>
        `;
    });
    
    articleListHTML += `
        </ul>
        <p><a href="${createUrl('index.html')}">&laquo; Back to all issues</a></p>
    `;
    
    contentDiv.innerHTML = articleListHTML;
}

// Display articles by a specific type
function displayTypeArticles(typeName) {
    const contentDiv = document.getElementById('content');
    
    // Filter articles by type
    const typeArticles = ARTICLES.filter(item => 
        (item.type || 'Other') === typeName
    ).sort((a, b) => a.date.localeCompare(b.date) || a.title.localeCompare(b.title));
    
    if (typeArticles.length === 0) {
        contentDiv.innerHTML = `
            <div class="error">
                <p>No articles found of type "${typeName}".</p>
                <p><a href="${createUrl('index.html')}">Return to issue list</a></p>
            </div>
        `;
        return;
    }
    
    let articleListHTML = `
        <div class="article-header">
            <div class="issue-title">Articles of type: ${typeName}</div>
        </div>
        <ul class="article-list">
    `;
    
    typeArticles.forEach(article => {
        // Get PDF path for this issue
        const pdfPath = getPdfPath(article.issue);
        
        articleListHTML += `
            <li>
                <div class="article-list-title">
                    <a href="${createUrl('index.html', {path: article.path})}">${article.title}</a>
                </div>
                <div class="article-list-meta">
                    ${article.author ? article.author.split(' ').map(name => 
                        `<a href="${createUrl('index.html', {author: name})}">${name}</a>`
                    ).join(' ') : ''}
                    <a href="${createUrl('index.html', {issue: article.issue})}">${article.issue}</a>
                    ${pdfPath ? `<a href="${pdfPath}" class="pdf-link" target="_blank" style="font-size: 0.8em; padding: 1px 4px;">PDF</a>` : ''}
                    ${article.type ? `<a href="${createUrl('index.html', {type: article.type})}">${article.type}</a>` : ''}
                </div>
            </li>
        `;
    });
    
    articleListHTML += `
        </ul>
        <p><a href="${createUrl('index.html')}">&laquo; Back to all issues</a></p>
    `;
    
    contentDiv.innerHTML = articleListHTML;
}

// Main function to determine what to display
function initializeDisplay() {
    const requestedPath = getUrlParam('path');
    const requestedIssue = getUrlParam('issue');
    const requestedAuthor = getUrlParam('author');
    const requestedType = getUrlParam('type');
    
    if (requestedPath) {
        // Display specific article
        displayArticle(requestedPath);
    } else if (requestedIssue) {
        // Display articles in a specific issue
        displayIssueArticles(requestedIssue);
    } else if (requestedAuthor) {
        // Display articles by a specific author
        displayAuthorArticles(requestedAuthor);
    } else if (requestedType) {
        // Display articles of a specific type
        displayTypeArticles(requestedType);
    } else {
        // Display list of issues
        displayIssueList();
    }
}

// Run when page loads
window.onload = function () {
    initLanguageToggle();

    const pdfScript = document.createElement('script');
    pdfScript.src = 'support/pdfs.js';
    pdfScript.onload = () => {
        initializeDisplay(); // only run after PDFs are available
    };
    pdfScript.onerror = () => {
        console.warn('⚠️ Failed to load pdfs.js. PDF links may not appear.');
        initializeDisplay(); // proceed anyway
    };

    document.body.appendChild(pdfScript);
};
