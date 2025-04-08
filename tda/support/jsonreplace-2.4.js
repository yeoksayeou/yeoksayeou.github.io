/**
 * Article Data Synchronization Script (jsonreplace)
 * ================================================
 * 
 * Overview:
 * ---------
 * This script enhances article metadata by updating the records in a data file
 * with more accurate title, author, and type information from a titles file.
 * It's designed to merge information from two different sources where the titles file
 * contains more reliable or up-to-date content.
 * 
 * Purpose:
 * --------
 * - Synchronizes article metadata between different data sources
 * - Replaces potentially incomplete or incorrect title, author, and type fields
 * - Maintains all other data fields from the original dataset
 * - Preserves the original JavaScript export/module structure
 * 
 * Input Files:
 * ------------
 * 1. Data File (default: 'data_en.js'):
 *    - Contains complete article records but may have incomplete/incorrect metadata
 *    - Expected to have a 'path' field with format: 'issue_name/article_id.txt'
 *    - Can be formatted as JSON array, JavaScript module export, or variable assignment
 * 
 * 2. Titles File (default: 'titles_en.js'):
 *    - Contains reliable metadata in a structured format
 *    - Expected to have 'issue', 'article-id', 'article-title', 'author', and optionally 'type' fields
 *    - Can be formatted as JSON array, JavaScript module export, or variable assignment
 * 
 * Matching Logic:
 * --------------
 * - Extracts issue number from the first part of the path (e.g., '01_issue_name' → '01')
 * - Extracts article ID from the second part of the path (e.g., 'article_id.txt' → 'article_id')
 * - Creates a lookup key combining issue number and article ID: 'issue/article-id'
 * - Finds matching entries in the titles file using this key
 * 
 * Fields Updated:
 * --------------
 * - title:  Set to article-title from the titles file
 * - author: Set to author from the titles file (or empty string if null)
 * - type:   Set to article-type from the titles file
 * 
 * Output:
 * -------
 * - Creates 'updated_data_en.js' with the merged data
 * - Tries to maintain the original file format (export statement, variable declaration, etc.)
 * - Reports statistics on matching success rate
 * 
 * Error Handling:
 * --------------
 * - Handles different JSON/JavaScript file formats through pattern matching
 * - Skips entries with invalid path formats
 * - Reports entries where no match was found
 * - Provides detailed console output for debugging
 * 
 * Usage:
 * ------
 * node jsonreplace-2.0.js [dataFilePath] [titlesFilePath]
 * 
 * Parameters:
 * - dataFilePath:   Path to the main data file (default: 'data_en.js')
 * - titlesFilePath: Path to the titles file (default: 'titles_en.js')
 * 
 * Examples:
 * ---------
 * // Use default filenames in current directory
 * node jsonreplace-2.0.js
 * 
 * // Specify custom file paths
 * node jsonreplace-2.0.js ./data/articles.js ./data/titles_updated.js
 */

const fs = require('fs');

// Read the JSON files
const dataFile = process.argv[2] || 'data_en.js';
const titlesFile = process.argv[3] || 'titles_en.js';

// Function to extract JSON content from files that might not be pure JSON
function extractJSONFromFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Try direct JSON parsing first
  try {
    return JSON.parse(content);
  } catch (e) {
    // If not valid JSON, try to extract JSON array pattern
    const match = content.match(/\[\s*\{[\s\S]*\}\s*\]/);
    if (match) {
      return JSON.parse(match[0]);
    }
    // If we can't find a JSON array, look for assignment or export
    const assignmentMatch = content.match(/(?:const|let|var|export)(?:\s+default)?\s+\w+\s*=\s*(\[\s*\{[\s\S]*\}\s*\])/);
    if (assignmentMatch) {
      return JSON.parse(assignmentMatch[1]);
    }
  }
  throw new Error(`Could not extract JSON from file: ${filePath}`);
}

console.log(`Reading data from ${dataFile}...`);
console.log(`Reading titles from ${titlesFile}...`);

// Extract the JSON data
let dataEntries, titlesEntries;
try {
  dataEntries = extractJSONFromFile(dataFile);
  titlesEntries = extractJSONFromFile(titlesFile);
} catch (error) {
  console.error(`Error extracting JSON: ${error.message}`);
  process.exit(1);
}

console.log(`Found ${dataEntries.length} data entries and ${titlesEntries.length} title entries.`);

// Create a lookup map for faster access to title entries
const titlesMap = {};
titlesEntries.forEach(titleEntry => {
  // Use issue (first column) as the first part of the key
  const key = `${titleEntry.issue}/${titleEntry["article-id"]}`;
  titlesMap[key] = titleEntry;
});

// Count how many entries we expect to match
let expectedMatches = 0;
dataEntries.forEach(dataEntry => {
  const pathParts = dataEntry.path.split('/');
  if (pathParts.length === 2) {
    expectedMatches++;
  }
});

console.log(`Expecting to match approximately ${expectedMatches} entries...`);

// Update the data entries with information from the titles
let matchCount = 0;
const updatedDataEntries = dataEntries.map(dataEntry => {
  // Extract issue and article-id from the path
  const pathParts = dataEntry.path.split('/');
  if (pathParts.length !== 2) {
    console.log(`Skipping entry with invalid path format: ${dataEntry.path}`);
    return dataEntry;
  }
  
  // Extract the issue part (first part before the slash)
  const issuePart = pathParts[0];
  
  // Try different formats for the issue number:
  // 1. Either extract digits before an underscore (e.g., "01_issueTitle" -> "01")
  // 2. Or use the whole string if it's just digits (e.g., "01" -> "01")
  let issueDigits;
  
  // Check if the issue part is just digits
  if (/^\d+$/.test(issuePart)) {
    // If the issue part is entirely digits, use it directly
    issueDigits = issuePart;
  } else {
    // Otherwise try to extract digits before an underscore
    const issueMatch = issuePart.match(/^(\d+)_/);
    if (!issueMatch) {
      console.log(`Skipping entry with unexpected issue format: ${issuePart}`);
      return dataEntry;
    }
    issueDigits = issueMatch[1];
  }
  // Extract article ID (second part, removing .txt extension)
  const articleId = pathParts[1].replace('.txt', '');
  
  // Create the lookup key using the first two digits of the issue and the article ID
  const lookupKey = `${issueDigits}/${articleId}`;
  
  // Find the matching title entry
  const matchingTitleEntry = titlesMap[lookupKey];
  
  if (matchingTitleEntry) {
    matchCount++;
    
    // Create a new object with updated fields
    return {
      ...dataEntry,
      title: matchingTitleEntry["article-title"],
      author: matchingTitleEntry.author !== null ? matchingTitleEntry.author : "",
      type: matchingTitleEntry["article-type"]
    };
  } else {
    console.log(`No match found for: ${lookupKey}`);
    return dataEntry;
  }
});

console.log(`Successfully matched and updated ${matchCount} entries (${Math.round(matchCount/dataEntries.length*100)}% of data).`);

// Get the original file structure to maintain it
const originalContent = fs.readFileSync(dataFile, 'utf8');
const outputFile = 'updated_data_en.js';
let outputContent;

// Try to maintain the original file format
if (originalContent.trim().startsWith('export default')) {
  outputContent = `export default ${JSON.stringify(updatedDataEntries, null, 2)};`;
} else if (originalContent.trim().match(/^export\s+const\s+\w+/)) {
  const varNameMatch = originalContent.match(/^export\s+const\s+(\w+)/);
  const varName = varNameMatch ? varNameMatch[1] : 'data';
  outputContent = `export const ${varName} = ${JSON.stringify(updatedDataEntries, null, 2)};`;
} else if (originalContent.trim().match(/^(const|let|var)\s+\w+/)) {
  const varNameMatch = originalContent.match(/^(const|let|var)\s+(\w+)/);
  const varType = varNameMatch ? varNameMatch[1] : 'const';
  const varName = varNameMatch ? varNameMatch[2] : 'data';
  outputContent = `${varType} ${varName} = ${JSON.stringify(updatedDataEntries, null, 2)};\n\nmodule.exports = ${varName};`;
} else {
  // Just write the plain JSON
  outputContent = JSON.stringify(updatedDataEntries, null, 2);
}

try {
  fs.writeFileSync(outputFile, outputContent);
  console.log(`Updated data written to ${outputFile}`);
} catch (error) {
  console.error(`Error writing output file: ${error.message}`);
  process.exit(1);
}
