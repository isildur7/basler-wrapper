from pypylon import pylon
from pypylon import genicam

def create_simple_camera(config_file_dir):
    """
    connects to the first available camera and reads in a configuration file. Create a configuration file
    using the pylon viewer, the most painless way to deal with camera configurations.

    Arguments:
    config_file_dir :   Path to the saved config file

    Returns:
    A Basler camera object
    """
    # conecting to the first available camera
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    print("Using device ", camera.GetDeviceInfo().GetModelName())
    camera.Open()
    # Read a camera cofiguration file into the camera
    # refer to https://github.com/basler/pypylon/issues/131
    print("Reading file back to camera's node map...")
    pylon.FeaturePersistence.Load(config_file_dir, camera.GetNodeMap(), True)

    return camera

def change_feature_map(camera, config_file_dir):
    pylon.FeaturePersistence.Load(config_file_dir, camera.GetNodeMap(), True)

    return camera

def start_imaging(camera):
    """
    starts grabbing images with the camera, must run this before actually taking images

    Arguments:
    camera :    camera object with which to start grabbing

    returns:
    None
    """
    # Latest Image strategy, none of the others seems suitable
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return

def stop_imaging(camera):
    """
    Stops grabbing images.

    Arguments:
    camera :    camera object to close

    Returns:
    None
    """
    # Releasing the resource    
    camera.StopGrabbing()

    return

def close_camera(camera):
    """
    Switch off the camera and release all resources. Run create to restart.

    Arguments:
    camera :    active camera object

    Returns:
    None
    """
    camera.Close()

    return

def opencv_converter():
    """
    Creates an image format converter for getting opencv BGR images.

    Arguments:
    None

    Returns:
    Converter object
    """
    converter = pylon.ImageFormatConverter()
    # converting to opencv bgr format
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    return converter

def take_one_opencv_image(camera, converter):
    """
    Obtains a single opencv RGB image from the camera. Camera object should be created and imaging
    should have been started. Converter must be an opencv converter.

    Arguments: 
    camera :    The camera object with which to take an image
    converter : opencv converter object, can be obtained using opencv_converter()

    returns:
    BGR opencv image array
    """
    try:
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        # Image grabbed successfully?
        if grabResult.GrabSucceeded():
            # convert the image
            image = converter.Convert(grabResult)
            # Access the image data
            img = image.GetArray()
        else:
            print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
        grabResult.Release()
    except genicam.GenericException as e:
        # Error handling.
        print("An exception occurred.")
        print(e.GetDescription())
        return
    
    return img

def change_ROI(camera, dimensions, offsets):
    """
    Change the camera ROI to capture only those pixels from the sensor.

    Arguments:
    camera :     active camera object
    dimensions : tuple of (width, height) of ROI in pixels
    offsets :    tuple of (x-offset, y-offset) from the left top corner in pixels

    returns:
    modified camera object
    """
    try:
        # Maximize the Image AOI.
        camera.Width = dimensions[0]
        camera.Height = dimensions[1]
        if genicam.IsWritable(camera.OffsetX):
            camera.OffsetX = offsets[0]
        if genicam.IsWritable(camera.OffsetY):
            camera.OffsetY = offsets[1]

    except genicam.GenericException as e:
        raise genicam.RuntimeException("Could not apply configuration. GenICam::GenericException \
                                        caught in OnOpened method msg=%s" % e.what())
        return
    
    return camera

def max_ROI(camera):
    """
    Set capture area to maximum available on the sensor.

    Arguments:
    camera :    active camera object

    Returns:
    modified camera object
    """
    try:
        # Maximize the Image AOI.
        if genicam.IsWritable(camera.OffsetX):
            camera.OffsetX = camera.OffsetX.Min
        if genicam.IsWritable(camera.OffsetY):
            camera.OffsetY = camera.OffsetY.Min
        camera.Width = camera.Width.Max
        camera.Height = camera.Height.Max

    except genicam.GenericException as e:
        raise genicam.RuntimeException("Could not apply configuration. GenICam::GenericException \
                                        caught in OnOpened method msg=%s" % e.what())
        return
    
    return camera

def capture_and_save_png(camera, filename):
    """
    Captures an image to save it as a png in the given path. Can also use opencv to saved any converted images.

    Arguments:
    camera :    Active camera object. It must be in imaging mode.
    filename :  Path to the image

    Returns:
    None
    """
    img = pylon.PylonImage()
    with camera.RetrieveResult(5000) as result:
        # Calling AttachGrabResultBuffer creates another reference to the
        # grab result buffer. This prevents the buffer's reuse for grabbing.
        img.AttachGrabResultBuffer(result)
        img.Save(pylon.ImageFileFormat_Png, filename)

        # In order to make it possible to reuse the grab result for grabbing
        # again, we have to release the image (effectively emptying the
        # image object)
        img.Release()

    return
    
                                