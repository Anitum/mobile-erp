import { test, expect } from '@playwright/test';

test.describe('Teacher Dashboard - Attendance Management', () => {
  // Setup for each test
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:5000/login');
    
    // Login as a teacher
    await page.fill('#email', 'teacher@school.com');
    await page.fill('#password', 'teacherpass123');
    await page.click('button[type="submit"]');
    
    // Verify successful login and navigation to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('.dashboard-title')).toContainText('Teacher Dashboard');
  });

  test('should display attendance page with correct elements', async ({ page }) => {
    // Navigate to attendance page
    await page.click('text=Attendance');
    
    // Verify essential elements are present
    await expect(page.locator('.date-picker')).toBeVisible();
    await expect(page.locator('.student-list')).toBeVisible();
    await expect(page.locator('.attendance-status-options')).toBeVisible();
    await expect(page.locator('button:text("Submit Attendance")')).toBeVisible();
  });

  test('should mark student attendance as present', async ({ page }) => {
    await page.click('text=Attendance');
    
    // Select today's date
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[type="date"]', today);
    
    // Find a specific student row and mark as present
    const studentRow = page.locator('.student-row').filter({ hasText: 'John Doe' });
    await studentRow.locator('select.attendance-status').selectOption('present');
    
    // Add check-in time
    await studentRow.locator('input.check-in-time').fill('09:00');
    
    // Add remarks
    await studentRow.locator('textarea.remarks').fill('On time');
    
    // Submit attendance
    await page.click('button:text("Submit Attendance")');
    
    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Attendance recorded successfully');
  });

  test('should mark student attendance as absent', async ({ page }) => {
    await page.click('text=Attendance');
    
    // Select today's date
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[type="date"]', today);
    
    // Find a specific student row and mark as absent
    const studentRow = page.locator('.student-row').filter({ hasText: 'Jane Smith' });
    await studentRow.locator('select.attendance-status').selectOption('absent');
    
    // Add remarks for absence
    await studentRow.locator('textarea.remarks').fill('Parent notified');
    
    // Submit attendance
    await page.click('button:text("Submit Attendance")');
    
    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Attendance recorded successfully');
  });

  test('should mark student attendance as late', async ({ page }) => {
    await page.click('text=Attendance');
    
    // Select today's date
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[type="date"]', today);
    
    // Find a specific student row and mark as late
    const studentRow = page.locator('.student-row').filter({ hasText: 'Mike Johnson' });
    await studentRow.locator('select.attendance-status').selectOption('late');
    
    // Add check-in time
    await studentRow.locator('input.check-in-time').fill('09:30');
    
    // Add remarks
    await studentRow.locator('textarea.remarks').fill('Traffic delay');
    
    // Submit attendance
    await page.click('button:text("Submit Attendance")');
    
    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Attendance recorded successfully');
  });

  test('should filter attendance by date range', async ({ page }) => {
    await page.click('text=Attendance Records');
    
    // Set date range
    await page.fill('input[name="start-date"]', '2024-01-01');
    await page.fill('input[name="end-date"]', '2024-01-31');
    await page.click('button:text("Filter")');
    
    // Verify filtered results
    await expect(page.locator('.attendance-record')).toHaveCount.greaterThan(0);
    await expect(page.locator('.no-records-found')).not.toBeVisible();
  });

  test('should export attendance report', async ({ page, context }) => {
    await page.click('text=Attendance Records');
    
    // Set up download listener
    const downloadPromise = page.waitForEvent('download');
    
    // Click export button
    await page.click('button:text("Export Report")');
    
    // Wait for download to start
    const download = await downloadPromise;
    
    // Verify file name contains 'attendance_report'
    expect(download.suggestedFilename()).toContain('attendance_report');
  });

  test('should handle bulk attendance marking', async ({ page }) => {
    await page.click('text=Attendance');
    
    // Select today's date
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[type="date"]', today);
    
    // Click "Mark All Present" button
    await page.click('button:text("Mark All Present")');
    
    // Verify all status dropdowns are set to "present"
    const statusDropdowns = await page.locator('select.attendance-status').all();
    for (const dropdown of statusDropdowns) {
      await expect(dropdown).toHaveValue('present');
    }
    
    // Submit attendance
    await page.click('button:text("Submit Attendance")');
    
    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Attendance recorded successfully');
  });

  test('should validate required fields', async ({ page }) => {
    await page.click('text=Attendance');
    
    // Try to submit without selecting date
    await page.click('button:text("Submit Attendance")');
    
    // Verify error message
    await expect(page.locator('.error-message')).toContainText('Please select a date');
    
    // Select date but try to submit without status
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[type="date"]', today);
    await page.click('button:text("Submit Attendance")');
    
    // Verify error message
    await expect(page.locator('.error-message')).toContainText('Please mark attendance status for all students');
  });

  test('should update existing attendance record', async ({ page }) => {
    await page.click('text=Attendance Records');
    
    // Find existing record and click edit
    await page.click('.attendance-record >> text="John Doe" >> .edit-button');
    
    // Update status
    await page.locator('select.attendance-status').selectOption('late');
    await page.locator('input.check-in-time').fill('09:45');
    await page.locator('textarea.remarks').fill('Updated: Bus delayed');
    
    // Save changes
    await page.click('button:text("Save Changes")');
    
    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Attendance updated successfully');
    
    // Verify changes are reflected
    await expect(page.locator('.attendance-record')).toContainText('late');
    await expect(page.locator('.attendance-record')).toContainText('09:45');
    await expect(page.locator('.attendance-record')).toContainText('Updated: Bus delayed');
  });
}); 