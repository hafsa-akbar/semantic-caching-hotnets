// Function to save image details to sessionStorage
function saveImageDetails() {
    sessionStorage.setItem('imageDetails', JSON.stringify(imageDetails));
}

// Function to load image details from sessionStorage
function loadImageDetails() {
    const savedData = sessionStorage.getItem('imageDetails');
    return savedData ? JSON.parse(savedData) : [];
}

// Load existing details (this will be empty after clearing session storage)
let imageDetails = loadImageDetails();

// Map to track image counts for each article
let imageCount = {};
let articleNumberMap = JSON.parse(sessionStorage.getItem('articleNumberMap')) || {}; // Load from sessionStorage
let currentArticleNumber = Object.keys(articleNumberMap).length + 1; // Set the next article number

// Function to get current article number based on URL
function getArticleNumber() {
    const url = window.location.pathname.split('/').pop();
    if (!articleNumberMap[url]) {
        articleNumberMap[url] = currentArticleNumber++; // Assign and increment the article number
        sessionStorage.setItem('articleNumberMap', JSON.stringify(articleNumberMap)); // Save updated map
    }
    return articleNumberMap[url];
}

// Function to set up image click event listeners
function setupImageClickListeners() {
    const articleNumber = getArticleNumber();
    
    // Initialize image count for the current article
    if (!imageCount[articleNumber]) {
        imageCount[articleNumber] = 0;
    }

    const images = document.querySelectorAll('img');

    images.forEach((img) => {
        img.addEventListener('click', () => {
            const headline = document.querySelector('h1')?.textContent || 'N/A';
            const articleUrl = window.location.href;

            // Increment image count for the current article
            const currentImageCount = ++imageCount[articleNumber];
            const imageNumber = `image_${articleNumber}_${currentImageCount}`;

            // Save only the required details
            const imageInfo = {
                article_heading: headline,  // Save the article heading
                img_src: img.src,           // Save the image source
                altText: img.alt,           // Save the alt text (optional, keep if needed)
                article_url: articleUrl      // Save the article URL
            };

            imageDetails.push(imageInfo);
            saveImageDetails();  // Save to sessionStorage
            console.log(`Added Image ${imageNumber}:`, imageInfo);
        });
    });
}

// Function to convert data to CSV and trigger download
function downloadCSV(data) {
    const csvContent = "data:text/csv;charset=utf-8," 
        + "article_heading,img_src,altText,article_url\n" // Updated header
        + data.map(({ article_heading, img_src, altText, article_url }) => 
            `"${article_heading}","${img_src}","${altText}","${article_url}"`
        ).join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "file_name.csv"); // Set the filename to labels.csv
    document.body.appendChild(link); // Required for Firefox

    link.click();
}

// Command to end selection and download CSV
const endSelection = () => {
    if (imageDetails.length > 0) {
        downloadCSV(imageDetails);
    } else {
        console.log("No images selected.");
    }
};

// Initial setup
setupImageClickListeners();

// Observe URL changes to setup listeners again
const observer = new MutationObserver(() => {
    setupImageClickListeners();
});

// Start observing the document for changes (e.g., when navigating to a new article)
observer.observe(document.body, { childList: true, subtree: true });

// Provide an instruction to the user
console.log("Click on images to select them. When done, run 'endSelection()' to download the CSV.");
