#!/usr/bin/evn python

"""
CMSC733 Spring 2019: Classical and Deep Learning Approaches for
Geometric Computer Vision
Project1: MyAutoPano: Phase 1 Starter Code

Author(s): 
Chahat Deep Singh (chahat@terpmail.umd.edu) 
PhD Student in Computer Science,
University of Maryland, College Park

Nitin J. Sanket (nitinsan@terpmail.umd.edu)
PhD Candidate in Computer Science,
University of Maryland, College Park
"""

#Code starts here:
import numpy as np
import matplotlib.pyplot as plt
import cv2
from skimage.feature import peak_local_max
import argparse
import os


#reads images 
def read_images(folder_name):
    print("Reading images from ", folder_name)
    images = []
    files = os.listdir(folder_name)	
    files = sorted(files)
    print("Found ", files)
    for file in files:
        image_path = folder_name + "/" + file
        image = cv2.imread(image_path)
        if image is not None:
            images.append(image)
        else:
            print("Error in loading image ", image)

    return images

#display image array
def showImageArray(img_array, file_name):
    
    image_array = img_array.copy()
    image_array = makeImageSameSize(image_array)
    concat = image_array[0].copy()

    for l in range(1,len(image_array)):
        image = image_array[l]
        concat = np.concatenate((concat,image), axis = 1)
        
    cv2.imshow(file_name, concat)
    cv2.waitKey() 
    cv2.destroyAllWindows()
    #cv2.imwrite(file_name, concat)
    
#detects corners using inbuilt methods    
def cornersDetection(imgs, choice):
    images = imgs.copy()
    print("detecting corners ...")
    detected_corners = []
    cmaps = []
    corner_images = []
    for i in images:
        image = i.copy()
        gray_image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        gray_image = np.float32(gray_image)


        if(choice == 1):
            print("using Harris corner detection method.")
            corner_strength = cv2.cornerHarris(gray_image,2,3,0.04)
            corner_strength[corner_strength<0.01*corner_strength.max()] = 0
            detected_corner = np.where(corner_strength>0.001*corner_strength.max())
            detected_corners.append(detected_corner)
            cmaps.append(corner_strength)
            image[corner_strength > 0.001*corner_strength.max()]=[0,0,255]
            corner_images.append(image)
        else:
            print("using Shi-Tomashi corner detection method.")
            dst = cv2.goodFeaturesToTrack(gray_image, 1000 ,0.01, 10)
            dst = np.int0(dst)
            detected_corners.append(dst)
            for c in dst:
                x,y = c.ravel()
                cv2.circle(image,(x,y),3,(0, 0, 255),-1) 
                          
            corner_images.append(image)
            cmap = np.zeros(gray_image.shape) #not sure what to do
            cmaps.append(cmap)
    #filter detected corners
    #remove the corner one
    return detected_corners, cmaps, corner_images

#Converts a 40x40 patch around the cornes to a 64x1 vector
def getFeatureDescriptor(gray_img,x,y, patch_size=40):
    gray_image = gray_img
    patch = gray_image[x-patch_size//2:x+patch_size//2, y-patch_size//2:y+patch_size//2] 
    # gaussian blur
    patch = cv2.GaussianBlur(patch,(3,3),0)
    # subsample to 20% size or 1/5th
    patch = cv2.resize(patch, None, fx=0.2, fy=0.2, interpolation = cv2.INTER_CUBIC)
    feature = patch.reshape(-1)
    feature = (feature-feature.mean())/ np.std(feature)
    return feature

#detects pairs of features that are similar 
def getPairs(img_1, img_2, all_corners_1, all_corners_2, patch_size = 40, alpha = 0.7):

    image_1 = img_1.copy()
    image_2 = img_2.copy()

    gray_image1 = cv2.cvtColor(image_1,cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image_2,cv2.COLOR_BGR2GRAY)

    width1, height1 = image_1.shape[:2]
    width2, height2 = image_2.shape[:2]

    print("width = ", width1, ", height = ", height1)
    print("width = ", width2, ", height = ", height2)

    features_1,features_2 = [], []
    corners_1, corners_2 = [],[]

    print("all corner 1 len = ", len(all_corners_1))
    print("all corner 2 len = ", len(all_corners_2))
    
    for corner in all_corners_1:
        x,y = corner.ravel()
        
        if (x - (patch_size / 2) > 0) & (x + (patch_size / 2) < height1) & (y - (patch_size / 2) > 0) & (y + (patch_size / 2) < width1):
            features_1.append(getFeatureDescriptor(gray_image1, y,x)) 
            corners_1.append([x,y])
        else:
            #print("ignored x, y", x, y)
            pass

    for corner in all_corners_2:
        x,y = corner.ravel()
        if (x - (patch_size / 2) > 0) & (x + (patch_size / 2) < height2) & (y - (patch_size / 2) > 0) & (y + (patch_size / 2) < width2):
            features_2.append(getFeatureDescriptor(gray_image2, y,x)) 
            corners_2.append([x,y]) 

    matched_pairs, match_level = [], []
    for i, feat_1 in enumerate(features_1):
        ssd = []  
        for j, feat_2 in enumerate(features_2):
            ssd.append(np.sum((feat_1 - feat_2)**2))
        top_matche = np.argmin(ssd)
#         if ssd[top_matches[0]] / ssd[top_matches[1]] < alpha:   
#             matched_pairs.append([corners_1[i] , corners_2[top_matches[0]]])
        matched_pairs.append([corners_1[i] , corners_2[top_matche]]) 
    print("matched pairs num = ", len(matched_pairs))
    matched_pairs = np.array(matched_pairs)
    return matched_pairs

#calculates anms using shi-tomas detector
def anmsshi(gray_image , best_features):
    corners = cv2.goodFeaturesToTrack(gray_image, 1000 ,0.01, 10)
    p , q, r,  = corners.shape
    s = 1e+6 *np.ones([p,3])
    ED = 0
    for i in range(p):
        for j in range(p):
            xi = int(corners[i,:,0])
            yi = int(corners[i,:,1])
            xj = int(corners[j,:,0])
            yj = int(corners[j,:,1])
            if gray_image[yi,xi] > gray_image[yj,xj]:
                ED = (xj - xi)**2 + (yj - yi)**2
            if ED < s[i,0]:
                s[i,0] = ED
                s[i,1] = xi
                s[i,2] = yi
    final = s[np.argsort(-s[:, 0])]
    sliced = final[:best_features,:]
    return sliced

#displays anms output

def anmsoutput(gray_image , color , best_feature):
	
	sliced = anmsshi(gray_image , best_feature)

	x = []
	y = []

	for i in range(best_feature):
		x1 = np.int0(sliced[i,1])
		y1 = np.int0(sliced[i,2])
		x.append(x1)
		y.append(y1)
	for i in range(best_feature):
		imag =cv2.circle(color , (x[i] , y[i]) , 2,(0,0,255) , -1)
		cv2.imshow('window_name', imag)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
	return imag , x , y 

#converts images to same size

def makeImageSameSize(imgs):
    images = imgs.copy()
    sizes = []
    for image in images:
        x, y, ch = image.shape
        sizes.append([x, y, ch])

    sizes = np.array(sizes)
    x_target, y_target, _ = np.max(sizes, axis = 0)
    
    images_resized = []

    for i, image in enumerate(images):
        image_resized = np.zeros((x_target, y_target, sizes[i, 2]), np.uint8)
        image_resized[0:sizes[i, 0], 0:sizes[i, 1], 0:sizes[i, 2]] = image
        images_resized.append(image_resized)

    return images_resized

#converts images to desired size
def makeImagesame(images , size):
    imgs = images.copy()
    x = size[0]
    y = size
    resize = []
    for i in range(len(imgs)):
        size = cv2.reshape(imgs[i], (x,y))
        resize.append(size)
    return resize


#displays feature matched
def showfeatureMatches(img_1, img_2, matched_pairs, file_name):

    image_1 = img_1.copy()
    image_2 = img_2.copy()

    image_1, image_2 = makeImageSameSize([image_1, image_2])

    concat = np.concatenate((image_1, image_2), axis = 1)
    corners_1 = matched_pairs[:,0].copy()
    corners_2  = matched_pairs[:,1].copy()
    corners_2[:,0] += image_1.shape[1]

    for (x1,y1) , (x2,y2) in zip(corners_1, corners_2):
        cv2.line(concat, (x1,y1), (x2,y2), (0, 0, 255), 1)
    
      
    cv2.imshow(file_name, concat)
    cv2.waitKey() 
    cv2.destroyAllWindows()
    cv2.imwrite(file_name, concat)


#draws features that matched
def drawmatches(img1 , img2 , matched_pairs , filename):
    image1 = img1.copy()
    image2 = img2.copy()

    image1 , image2 - makeImageSameSize([image1 , image2])
    corners1 = matched_pairs[:,0].copy()
    corners2 = matched_pairs[:,1].copy()

    corners2[:,0] += image1.shape[1]

    for i in range(len(corners1)):
        match  = cv2.drawMatches(image1 , corners1 , image2 , corners2)
    
    cv2.imshow(filename , match)
    cv2.waiyKey()
    cv2.destroyAllWindows()
    cv2.write(filename , match)


    
def testshowfeatureMatches(image_1, image_2, width = 20):
    matched_pairs= []
    I = np.linspace(10, 100, 10)
    for i in I:
        x1 = i
        y1 = i
        corner1 = np.int0(np.array([x1, y1]))

        x2 = i
        y2 = i
        corner2 = np.int0(np.array([x2, y2]))
        matched_pairs.append([corner1 , corner2])

    matched_pairs = np.array(matched_pairs)
    showfeatureMatches(image_1, image_2, matched_pairs, partition_width = 20)
    
    
#uses ransac to remove outliers
def removeOutliers(matched_pairs, outliers, accuracy, thresh):

    set1 = matched_pairs[:, 0]
    set2 = matched_pairs[:, 1]

    N_best = 0
    H_best = np.zeros([3, 3])
    
    e = outliers / set1.shape[0]
    s = 4
    p = accuracy
    iterations = np.log(1 - p) / np.log(1 - np.power((1 - e), s))
    iterations = np.int(iterations)
    iterations = 4000

    filtered_pair_indices = []

    print("iterations = ", iterations)
    for i in range(iterations):
        #randomly select four points
        n_rows = set1.shape[0]
        random_indices = np.random.choice(n_rows, size=4)

        set1_random = set1[random_indices]
        set2_random = set2[random_indices]
              
        #compute homography
        H = cv2.getPerspectiveTransform(np.float32(set1_random), np.float32(set2_random))

        set1_dash = np.vstack((set1[:,0], set1[:,1], np.ones([1, n_rows])))
        set1_transformed_dash = np.dot(H, set1_dash)
        
        t1 = set1_transformed_dash[0,:]/set1_transformed_dash[2,:]
        t2 = set1_transformed_dash[1,:]/set1_transformed_dash[2,:]

        set1_transformed = np.array([t1, t2]).T

        E = calculateError(set2, set1_transformed)
        
     
        E[E <= thresh] = 1
        E[E > thresh] = 0
    
    
        N = np.sum(E)


        if N > N_best:
            N_best = N
            H_best = H
            filtered_pair_indices = np.where(E == 1)
    
    filtered_set1 =  set1[filtered_pair_indices]
    filtered_set2 =  set2[filtered_pair_indices]

    print("Number of pairs after filtering = ", filtered_set1.shape[0])

    filter_matched_pairs = np.zeros([filtered_set1.shape[0], filtered_set1.shape[1], 2])

    filter_matched_pairs[:, 0, :] = filtered_set1
    filter_matched_pairs[:, 1, :] = filtered_set2

    filter_matched_pairs = filter_matched_pairs.astype(int)

    H_inbuit, _ = cv2.findHomography(set1, set2)
    print("inbuilt = ", H_inbuit)
    print("Computed = ", H_best)

    return H_best, filter_matched_pairs


#calculate norm error
def calculateError(set1, set2):
   
    Err = np.zeros(set1.shape[0])
    tmp = set2 - set1
    num = set1.shape[0]

    for n in range(num):
        Err[n] = np.linalg.norm(tmp[n])
    return Err


#anms implementation
def activeNonMaximalSuppression(imgs, C_maps, N_best):
    
    images = imgs.copy()
    anms_img = []
    anms_corners = []
    for i,image in enumerate(images):

        cmap = C_maps[i]
        local_maximas = peak_local_max(cmap, min_distance=10)
        n_strong = local_maximas.shape[0]
        
        r = [np.Infinity for i in range(n_strong)]
        x=np.zeros((n_strong,1))
        y=np.zeros((n_strong,1))
        eu_dist = 0

        for i in range(n_strong):
            for j in range(n_strong):
                x_j = local_maximas[j][0]
                y_j = local_maximas[j][1]

                x_i = local_maximas[i][0]
                y_i = local_maximas[i][1]

                if(cmap[x_j, y_j] > cmap[x_i, y_i]):
                    eu_dist = np.square(x_j - x_i) + np.square(y_j - y_i)
                if r[i] > eu_dist:
                    r[i] = eu_dist
                    x[i] = x_j
                    y[i] = y_j

        index = np.argsort(r)
        index = np.flip(index)
        index = index[0:N_best]
        x_best=np.zeros((N_best,1))
        y_best=np.zeros((N_best,1))

        for i in range(N_best):
            x_best[i] = np.int0(x[index[i]])
            y_best[i] = np.int0(y[index[i]]) 
            cv2.circle(image, (y_best[i], x_best[i]), 3, (0, 255, 0), -1)

        anms_corner = np.int0(np.concatenate((x_best, y_best), axis = 1))
        anms_corners.append(anms_corner)
        anms_img.append(image)
    return anms_corners, anms_img



#stich images using homography
def stichimages(img0, img1, H):

    image0 = img0.copy()
    image1 = img1.copy()

    #stitch image 0 on image 1
    print("shapes")
    print(image0.shape)
    print(image1.shape)
    

    h0 ,w0 ,_ = image0.shape
    h1 ,w1 ,_ = image1.shape

    points_on_image0 = np.float32([[0, 0], [0, h0], [w0, h0], [w0, 0]]).reshape(-1,1,2)
    points_on_image0_transformed = cv2.perspectiveTransform(points_on_image0, H)
    print("transformed points = ", points_on_image0_transformed)
    points_on_image1 = np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1,1,2)

    points_on_merged_images = np.concatenate((points_on_image0_transformed, points_on_image1), axis = 0)
    points_on_merged_images_ = []

    for p in range(len(points_on_merged_images)):
        points_on_merged_images_.append(points_on_merged_images[p].ravel())

    points_on_merged_images_ = np.array(points_on_merged_images_)

    x_min, y_min = np.int0(np.min(points_on_merged_images_, axis = 0))
    x_max, y_max = np.int0(np.max(points_on_merged_images_, axis = 0))

    print("min, max")
    print(x_min, y_min)
    print(x_max, y_max)

    
    H_translate = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]]) 

    image0_transformed_and_stitched = cv2.warpPerspective(image0, np.dot(H_translate, H), (x_max-x_min, y_max-y_min))
    image0_transformed_and_stitched[-y_min:-y_min+h1, -x_min: -x_min+w1] = image1
    return image0_transformed_and_stitched

#crop images 

def cutImage(image):
    
    img = image.copy()
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    _,thresh = cv2.threshold(gray,5,255,cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x,y,w,h = cv2.boundingRect(contours[len(contours)-1])
    crop = img[y:y+h,x:x+w]

    return crop

def mergeImages(img_array, choice, save_folder_name, n, show_steps = True):

    image_array = img_array.copy()
    N = len(image_array)

    image0 = image_array[0]
    for i in range(1, N):

        print("processing image ", i)
        image1 = image_array[i] 

        image_pair = [image0, image1]
        
        detected_corners, cmaps, corner_images = cornersDetection(image_pair, choice)
        if show_steps:
            showImageArray(corner_images, save_folder_name + "/corners" + str(n+1) + ".png")
        """
        Perform ANMS: Adaptive Non-Maximal Suppression
        Save ANMS output as anms.png
        """
        if (choice == 1):
            print("Applying ALMS.")
            detected_corners, anms_image = activeNonMaximalSuppression(image_pair, cmaps, 500)
            if show_steps:
                showImageArray(anms_image, save_folder_name + "/anms_output" + str(n) + ".png")
        else:
            print("goodFeaturesToTrack is already using ALMS.") #review

        detected_corners0 = detected_corners[0]
        detected_corners1 = detected_corners[1]
                
        matched_pairs = getPairs(image0, image1, detected_corners0, detected_corners1, patch_size = 40, alpha = 0.9 )
        if show_steps:
            showfeatureMatches(image0, image1, matched_pairs, save_folder_name + "/matched_pairs" + str(n) + ".png")
        """
        Refine: RANSAC, Estimate Homography
        """
        H,filtered_matched_pairs = removeOutliers(matched_pairs, 20, 0.9, 5)
        if show_steps:
            showfeatureMatches(image0, image1, filtered_matched_pairs, save_folder_name + "/filtered_matched_pairs" + str(n) + ".png")
        """
        Image Warping + Blending
        Save Panorama output as mypano.png
        """
        stitched_image = stichimages(image0, image1, H)
        stitched_image = cutImage(stitched_image)
        if show_steps:
            cv2.imshow(save_folder_name + "/pano" + str(n+1) + ".png", stitched_image)
            cv2.waitKey() 
            cv2.destroyAllWindows()

        cv2.imwrite(save_folder_name + "/pano" + str(n+1) + ".png", stitched_image)
        image0 = stitched_image

    return image0

def MyAutoPano():

    Parser = argparse.ArgumentParser()
    Parser.add_argument('--BasePath', default="/Users/sheriarty/Downloads/Phase1/", help='base path')
    Parser.add_argument('--ImageDataFolder', default='Data/Train/Set2', help='folder for images')
    Parser.add_argument('--SaveFolder', default='Code/results', help='Folder to save results')
    # Parser.add_argument('--ShowImages', type = bool, default= True, help='show images or not')
    Args = Parser.parse_args()
    
    
    
    Args = Parser.parse_args()
    BasePath = Args.BasePath
    ImageDataFolder = Args.ImageDataFolder
    SaveFolder = Args.SaveFolder
    # ShowImages = Args.ShowImages
    ShowImages = True

    
    GoStepbyStep = False
    # Linux
    # BasePath = "/home/sheriarty/CMSC 733/pdave1_p1/Phase1/"

    #Mac
    # BasePath = "/Users/sheriarty/Downloads/Phase1/"
    # ImageDataFolder = 'Data/Train/Set2'
    # SaveFolder = 'Code/results/'
    # ShowImages = True

    use_harris = False


    images = read_images(BasePath + ImageDataFolder)
    if ShowImages:
        showImageArray(images, BasePath + ImageDataFolder + "/input.png")

    N = len(images)
    N_images = len(images)

    choice = 2
    if use_harris:
        choice = 1

    N1 = round(N_images/2)
    N2 = N_images - N1
    print(N1, " and ", N2)

    if not GoStepbyStep:
        while N_images is not 2:
            print("N = ", N_images, " N_half = ", N1)
            merged_images = []
            for n in range(0, N1, 2):
                if (n+1) <= N1:
                    img_array = images[n:n+2]
                    print("combining: ", n, n+1)
                    I = mergeImages(img_array, choice, BasePath + SaveFolder, n, ShowImages)
                    merged_images.append(I)
                else:
                    print("adding: ", n)
                    merged_images.append(images[n])

            for n in range(N1, N_images, 2):
                if (n+1) < N_images:
                    img_array = images[n:n+2]
                    img_array.reverse()
                    print("combining: ", n+1, n)
                    I = mergeImages(img_array, choice, BasePath + SaveFolder, n, ShowImages)
                    merged_images.append(I)
                else:
                    print("adding: ", n)
                    merged_images.append(images[n])
        
            images = merged_images
            N_images = len(images)
            N1 = round(N_images/2)
            N2 = N_images - N1
        
        print("final merging")
        if N % 2 != 0:
            print("reversing")
            merged_images.reverse()
        final = mergeImages(merged_images, choice, BasePath + SaveFolder, 100, ShowImages)
    else:
        Image0 = images[0]
        for n in range(N_images - 1):
            img_array = [Image0, images[n+1]]
            Image0 = mergeImages(img_array, choice, BasePath + SaveFolder, n, ShowImages)

        if ShowImages:
            cv2.imshow(BasePath + SaveFolder + "/pano" + str(n+1) + ".png", Image0)
            cv2.waitKey() 
            cv2.destroyAllWindows()

        cv2.imwrite(BasePath + SaveFolder + "/pano" + str(n+1) + ".png", Image0)


if __name__ == '__main__':
    MyAutoPano()
    
