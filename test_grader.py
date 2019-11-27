from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-i" , "--image", required=True, help="path to the input image")
args = vars(ap.parse_args())

# The answer key of the our set
ANSWER_KEY = {0: 1, 1: 4, 2: 0, 3: 3, 4: 1}

image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5,5),0)
edged = cv2.Canny(blurred, 75, 200)

# contours for the paper's edges
cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
docCnt = None

# to ensure that at least one contour was found
if len(cnts) > 0: 
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    # loop over sorted contours
    for c in cnts:
        
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # if len(approx) == 4, we can say that we have found the paper
        if (len(approx) == 4): 
            docCnt = approx
            break

            
paper = four_point_transform(image, docCnt.reshape(4, 2))
warped = four_point_transform(gray, docCnt.reshape(4, 2))

# # binarization/ thresholding the foreground from background
thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

# find contours in the threshold image
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
questionCnts = []

for c in cnts: 
    	# compute the bounding box of the contour to derive the aspect ratio
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        
        # adjust the size for the label the contour
        if (w >= 20 and h >= 20 and ar >= 0.9 and ar <= 1.1): 
            questionCnts.append(c)

# sort question contours from top-to-bottom
questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
correct = 0

# each question has 5 possible answers, so loop over the question in batches of 5
for(q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
    cnts = contours.sort_contours(questionCnts[i:i + 5])[0]
    bubbled = None

    for (j, c) in enumerate(cnts):
        # build a mask which reveals the current bubble onlyl for the question
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)
        
        # count the number of non-zero pixels in the bubble area
        mask = cv2.bitwise_and(thresh, thresh, mask=mask)
        total = cv2.countNonZero(mask)
        
        if bubbled is None or total > bubbled[0]:
            bubbled = (total, j)
            
    color = (0,0,255)
    k = ANSWER_KEY[q]
            
    if k == bubbled[1]:
        color = (0,255,0)
        correct += 1
        
    cv2.drawContours(paper, [cnts[k]], -1, color, 3)

# showing the result on the screen
score = (correct / 5.0) * 100
print("Score: {:.2f}%".format(score))
cv2.putText(paper, "{:.2f}%".format(score), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
cv2.imshow("Exam", paper)
cv2.waitKey(0)