// Pcd2Ply.cpp : 定义控制台应用程序的入口点。

#include <pcl/io/pcd_io.h>
#include <pcl/io/ply_io.h>
#include<pcl/PCLPointCloud2.h>
#include<iostream>
#include<string>

using namespace pcl;
using namespace pcl::io;
using namespace std;
 
int PCDtoPLYconvertor(string & input_filename ,string& output_filename)
{
pcl::PCLPointCloud2 cloud;
if (loadPCDFile(input_filename , cloud) < 0)
{
cout << "Error: cannot load the PCD file!!!"<< endl;
return -1;
}
PLYWriter writer;
writer.write(output_filename, cloud, Eigen::Vector4f::Zero(), Eigen::Quaternionf::Identity(),true,true);
return 0;

}

int main(int argc, char** argv)
{
string input_filename = "clear.pcd";
string output_filename = "clear.ply";
PCDtoPLYconvertor(input_filename , output_filename);
return 0;
}
